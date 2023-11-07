
import time
from app.apis.analyzer.analyzer import Stimulus
from app.apis.analyzer.analyzer import get_api_credentials
# from app.apis.analyzer.analyzer import Stimulus
import re
from os import remove

from app.model.analyzer_model import ApiCredential
from app.model.attention_model import StudySettings
from app.model.api_model import Apis
import os
import json
import pymongo
from app.apis.s3.s3manager import S3Manager
import hashlib

from datetime import datetime
import requests


BACKEND = 'https://analyzerapi.troiatec.com'
client = pymongo.MongoClient('172.17.0.1:27017')

def analyze(stimulus: Stimulus, token: str, credentials:ApiCredential, settings:StudySettings, userCreation = None):
    split_up = os.path.splitext(stimulus.image_url)

    try:
        now = datetime.now()
        originalName = f'{stimulus.title}{split_up[1]}' #getStimulus["title"] + split_up[1]
        extension = ''
        tipo = 0
        if (".png" in originalName or ".PNG" in originalName):
            extension = '.png'
            originalName = originalName[0: len(originalName) - 4]
        elif (".jpg" in originalName or ".JPG" in originalName):
            extension = '.jpg'
            originalName = originalName[0: len(originalName) - 4]
        elif (".jpeg" in originalName or ".JPEG" in originalName):
            extension = '.jpeg'
            originalName = originalName[0: len(originalName) - 5]
        elif (".mp4" in originalName or ".MP4" in originalName):
            extension = '.mp4'
            originalName = originalName[0: len(originalName) - 4]
            tipo = 1

        subexp = re.sub('[^A-Za-z0-9]+','',re.sub('\s+', '-', (originalName).lower()))
        fileName = f'Attention{now.strftime("%d%m%Y_%H%M%S")}{subexp}{extension}'

        print(f'corto {fileName}')
        
        img_data = requests.get(stimulus.image_url).content
        hash = hashlib.sha256(img_data).hexdigest()
        with open(fileName, 'wb') as f:
            f.write(img_data)

    except Exception as ex:
        print(ex)
        return {"message": "Error uploading the file"}
    finally:
        f.close()
    
    data = settings.dict()

    #TODO esto deberia tomarse desde las configuraciones del api en la bd
    objeto = {"image_hash": hash
                , "image_url": stimulus.image_url }

    data['tasks[0]'] = "focus"
    data['tasks[1]'] = "clarity_score"


    # fo = open(RootPath + fileName, 'rb')
    fo = open(fileName, 'rb')
    file = {'file': fo} # la ruta debe ser cambiada por la ruta del servidor
    headers = {'Api-key': credentials.clave}
    r = requests.post(url=credentials.url, files=file ,data=data, headers=headers)

    jsonResponse = r.json()
    print(f'attention respondio')
    print(jsonResponse)

    fo.close()
    if ("success" in str(jsonResponse)):
        study_id = (jsonResponse["data"]["study_id"]).strip('\"')
        remove(fileName)

        t_end = time.time() + (30 * 1)
        finished = False
        while(time.time() < t_end):
            status = requests.get(url=f'{credentials.url}/{study_id}/status', headers=headers)
            if not(status is None):
                status = status.json()
                if(status["data"]["status"] == "finished"):
                    finished = True
                    break
        

        if(finished):
            size = 0
            mapsArr = ['heatmap', 'focus']
            print(study_id)
            for mapa in mapsArr:
                headers = {'Api-key': credentials.clave}
                map = requests.get(url=f'{credentials.url}/{study_id}/image?image={mapa}', headers=headers)
        
                actualFname = f'{stimulus.title}_attention_{mapa}.jpg'

                with open(actualFname, 'wb') as f:
                    f.write(map.content)

                size += os.path.getsize(actualFname)

                data = {"idStimulus": stimulus.id_stimulus
                        , "n": f"attentionInsights_{mapa}" #+ mapsArr[mapaux]
                        , "api": Apis.ATTENTION.value} 

                if userCreation != None:
                    data.update({'userCreation': userCreation})

                fo = open(actualFname, 'rb')
                file = {'file': fo} # la ruta debe ser cambiada por la ruta del servidor
                headers = {'Authorization': f'Bearer {token}'}
                r = requests.post(url= f'{BACKEND}/Stimulus/SaveAndUploadAStimulusV2', files=file ,data=data, headers=headers)
                jsonResponse = r.json()

                print(jsonResponse)

                if(str(jsonResponse) == "successful"):
                    fo.close()
                    remove(actualFname)

            
        #obtener y guardar los scores

            headers = {'Api-key': credentials.clave}
            scores = requests.get(url=f'{credentials.url}/{study_id}', headers=headers)
            arrScore = scores.json()


            #TODO: esto se debe pasar al manejador de analyzer
            data = {'api': Apis.ATTENTION.value}
            headers = {'Authorization': f'Bearer {token}'}
            ApiMetrics = requests.post(url= f"{BACKEND}/Stimulus/getApiMetrics",data=data, headers=headers)

            print(ApiMetrics.text)
            ApiMetrics = json.loads(ApiMetrics.text)
            print(ApiMetrics[0]["id"])
            print(len(ApiMetrics))

            metricsids = []

            apiaux = 0

            while(apiaux < len(ApiMetrics)):
                metricsids.append(ApiMetrics[apiaux]["id"])
                apiaux = apiaux + 1

            
            i = 0
            #TODO: falto cambiar esto por una mejor forma de iterar, esto va con el todo anterior
            while(i < len(metricsids)):
                
                data = {"value": arrScore["data"]["aesthetics"]["clarity_score"]
                        , "idMetric": metricsids[i]
                        , "idStimulus": stimulus.id_stimulus}

                objeto.update({"clarity": arrScore["data"]["aesthetics"]["clarity_score"]})

                if userCreation != None:
                    data.update({"userCreation": userCreation})

                headers = {'Authorization': f'Bearer {token}'}
                r = requests.post(url= f"{BACKEND}/Stimulus/AddToScore",data=data, headers=headers)
                jsonResponse = r.json()

                if("inserted" not in(jsonResponse)):
                    return "fail"
            
                i = i + 1

            #save size of stimulus
            data = {'idStimulus': stimulus.id_stimulus, 'size': size}
            headers = {'Authorization': token}

            size = requests.post(url=f"{BACKEND}/Stimulus/UpdateSize",data=data, headers=headers)
            
            return objeto

    else:
        remove(fileName)
        return {"message": f"{jsonResponse}"}
    
    return "something gone wrong" #await "something gone wrong"





def get_dataset(set: str, credentials, max:int=100):

    attention_mongo = client.get_database('analyzer').get_collection('attention')
    s3m = S3Manager()
    s3_objects = s3m.s3_list_files(set)

    print(len(s3_objects))

    for obj in s3_objects:
        if max == 0:
            break
        else:
            max -= 1


        image_url = f"https://geotec-dev.s3.amazonaws.com/{obj.key}"
        image_request = requests.get(image_url)
        nombrecin = obj.key.split('/')[-1]

        settings = StudySettings(study_name=nombrecin, study_type='general', content_type='general')
        print(nombrecin)

        # b.Object('geotec-dev', f'dataset/Stimuli/{set}/{nombrecin.split(".")[0]}_feng_maps/{nombrecin}').put(Body=open('huecada.png', 'rb'))

        # if(image_request.status_code == 200):
        print(f"si existe: {image_url}")
        hash = hashlib.sha256(image_request.content).hexdigest()
        print(hash)


        existe = attention_mongo.find_one({"image_hash": hash})
        if not existe:
            print("no existe")
            objeto = {"image_hash": hash
                        , "image_url": image_url }

            config = settings.dict()
            #TODO esto deberia tomarse desde las configuraciones del api en la bd
            config['tasks[0]'] = "focus"
            config['tasks[1]'] = "clarity_score"


            file = {'file': image_request.content} # la ruta debe ser cambiada por la ruta del servidor
            headers = {'Api-key': credentials.clave}
            r = requests.post(url=credentials.url, files=file ,data=config, headers=headers)
            attention_response = r.json()

            print(f'attention respondio')
            print(attention_response)

            if ("success" in attention_response):

                study_id = (attention_response["data"]["study_id"]).strip('\"')

                t_end = time.time() + (30 * 1)
                finished = False

                while(time.time() < t_end):
                    status = requests.get(url=f'{credentials.url}/{study_id}/status', headers=headers)
                    print('esperando ...')

                    if not(status is None):
                        status = status.json()
                        if(status["data"]["status"] == "finished"):
                            finished = True
                            break


                
                size = 0
                mapsArr = ['heatmap', 'focus']
                print(study_id)

                for mapa in mapsArr:
                    headers = {'Api-key': credentials.clave}
                    map = requests.get(url=f'{credentials.url}/{study_id}/image?image={mapa}', headers=headers)
                    print(map)
            
                    actualFname = f'{nombrecin.split(".")[0]}_attention_{mapa}.jpg'
                    s3m.s3_save_object(collection=set, api='attention', name=nombrecin.split('.')[0], filename=actualFname, file=map.content)
                    # size += os.path.getsize(actualFname)




                    # if(str(jsonResponse) == "successful"):

                headers = {'Api-key': credentials.clave}
                scores = requests.get(url=f'{credentials.url}/{study_id}', headers=headers)
                arrScore = scores.json()
                print(arrScore)
                objeto.update({"clarity": arrScore["data"]["aesthetics"]["clarity_score"]})

            # headers = {'Authorization': f'Basic {credentials.clave}'}
            # r = requests.post(url=credentials.url, json=jsonrpc, headers=headers)
            # objeto = {"image_hash": hash
            #             , "image_url": image_url }

            # feng_response = r.json()['result'] 
            # objeto.update(feng_response)
            # id = feng_response['imageID']

            # mapsArr = ['gazeplot', 'aoi', 'heatmap', 'opacity', 'aes', 'raw_vf', 'raw']
            # for map in mapsArr:
            #     filen = id.replace(".png", f"_{map}.png")
            #     url_feng = f'https://service.feng-gui.com/users/erick.moreno.troiatec.com/files/images/{filen}'
            #     image = requests.get(url_feng).content

            #     s3m.s3_save_object(collection=set, api='feng', name=nombrecin.split('.')[0], filename=filen, file=image)

            # print(objeto)
            attention_mongo.insert_one(objeto)
    
    return {}