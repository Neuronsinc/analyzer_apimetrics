import requests
# from PIL import Image, ImageDraw, ImageFont

import hashlib
import pymongo
import boto3
from keras.models import load_model
import numpy as np
# model = load_model('model.h5')

from app.model.analyzer_model import Stimulus
from app.model.analyzer_model import ApiCredential
from app.model.api_model import Apis

from app.apis.s3.s3manager import S3Manager

from os import remove
import os
import json
import csv
import datetime


model = load_model('app/keras_models/Modelo.keras')
# input_array = np.array([[10,10]])
# x = model.predict(input_array)
# print(x)

BACKEND = 'https://analyzerapi.troiatec.com'
#BACKEND = 'http://localhost/Analyzer/Predict_Analyzer_Back'
client = pymongo.MongoClient('172.17.0.1:27017')


def get_dataset(set: str,credentials, max:int=100):

    feng_mongo = client.get_database('analyzer').get_collection('feng')
    print(feng_mongo)

    s3m = S3Manager()
    s3_objects = s3m.s3_list_files(set)
    print(len(s3_objects))

    for obj in s3_objects:
        if max == 0:
            break
        else:
            max += 1

        print(obj)
        image_url = f"https://geotec-dev.s3.amazonaws.com/{obj.key}"
        image_request = requests.get(image_url)
        nombrecin = obj.key.split('/')[-1]
        print(nombrecin)

        # b.Object('geotec-dev', f'dataset/Stimuli/{set}/{nombrecin.split(".")[0]}_feng_maps/{nombrecin}').put(Body=open('huecada.png', 'rb'))

        # if(image_request.status_code == 200):
        print(f"si existe: {image_url}")
        hash = hashlib.sha256(image_request.content).hexdigest()
        print(hash)

        jsonrpc = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "ImageAttention",
            "params": { "InputImage" : image_url #getStimulus['imageUrl']
                        , "viewType" : 0
                        , "ViewDistance" : 1
                        , "analysisOptions" : 0
                        , "outputOptions" : 111
            }
        }

        existe = feng_mongo.find_one({"image_hash": hash})
        if not existe:
            print("no existe")
            headers = {'Authorization': f'Basic {credentials.clave}'}
            r = requests.post(url=credentials.url, json=jsonrpc, headers=headers)
            objeto = {"image_hash": hash
                        , "image_url": image_url }

            feng_response = r.json()['result'] 
            objeto.update(feng_response)
            id = feng_response['imageID']

            mapsArr = ['gazeplot', 'aoi', 'heatmap', 'opacity', 'aes', 'raw_vf', 'raw']
            for map in mapsArr:
                filen = id.replace(".png", f"_{map}.png")
                url_feng = f'https://service.feng-gui.com/users/erick.moreno.troiatec.com/files/images/{filen}'
                image = requests.get(url_feng).content

                s3m.s3_save_object(collection=set, api='feng', name=nombrecin.split('.')[0], filename=filen, file=image)

            print(objeto)
            feng_mongo.insert_one(objeto)
    
    return {}


# def analyze_file(api:str , getStimulus, idStimulus, token, userCreation = None):
def analyze(stimulus: Stimulus, clarity: float, token: str, credentials:ApiCredential, userCreation = None):
    print('analizando feng')
    jsonrpc = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "ImageAttention",
        "params": { "InputImage" : stimulus.image_url #getStimulus['imageUrl']
                    , "viewType" : 0
                    , "ViewDistance" : 1
                    , "analysisOptions" : 960
                    , "outputOptions" : 69
        }
    }
    
    # headers = {'Authorization': f'Basic {api_credentials["clave"]}'}
    # r = requests.post(url=api_credentials["url"], json=jsonrpc, headers=headers)
    headers = {'Authorization': f'Basic {credentials.clave}'}
    r = requests.post(url=credentials.url, json=jsonrpc, headers=headers)
    print(r)
    FengResponse = r.json()
    print(FengResponse['result'])

    if ("result" in FengResponse):
        #size = 0
        mapsArr = ['gazeplot', 'aoi', 'heatmap', 'opacity']
        namesMap = {}
        id = FengResponse['result']['imageID']
        print(f'id {id}')

        # while(mapaux < len(mapsArr)):
        for mapa in mapsArr:
            # headers = {'Authorization': 'Basic ' + api_credentials["clave"]}
            headers = {'Authorization': f'Basic {credentials.clave}'}
            # url_feng = f'https://service.feng-gui.com/users/erick.moreno.troiatec.com/files/images/{id.replace(".png", "_" + mapsArr[mapaux] + ".png")}'
            #OBTIENE LA IMAGEN
            url_feng = f'https://service.feng-gui.com/users/erick.moreno.troiatec.com/files/images/{id.replace(".png", "_" + mapa + ".png")}'
            map = requests.get(url= url_feng, headers=headers)
        
            # actual_filename = getStimulus["title"] + '_feng_' + mapsArr[mapaux] +'.png'
            actual_filename = f'{stimulus.title}_feng_{mapa}.png'# + '_feng_' + mapa +'.png'
            print(map)
            with open(actual_filename, 'wb') as f:
                f.write(map.content)
            
            namesMap[mapa] = actual_filename

            # RemoveWatermark(actual_filename, mapsArr[mapaux], getStimulus["title"] + '_feng_' + mapsArr[mapaux])
            # RemoveWatermark(actual_filename, mapa, f'{stimulus.title}_feng_{mapa}')

            # size += os.path.getsize(RootPath + actual_filename)
            #size += os.path.getsize(actual_filename)

            #data = {"idStimulus": stimulus.id_stimulus
            #    , "n": f"fengGui_{mapa}"
            #    , "api": 3}

            #if userCreation != None:
                # data.update({"userCreation": userCreation})
            #    data["userCreation"]= userCreation

            #fo = open(actual_filename, 'rb')
            #file = {'file': fo} # la ruta debe ser cambiada por la ruta del servidor
            #headers = {'Authorization': f'Bearer {token}'}
            #url_upload = f'{BACKEND}/Stimulus/SaveAndUploadAStimulusV2'
            # r = requests.post(url=Backend + "/Stimulus/SaveAndUploadAStimulusV2", files=file ,data=data, headers=headers)
            #r = requests.post(url=url_upload, files=file ,data=data, headers=headers)
            #jsonResponse = r.json()

            #print(jsonResponse)

            #if(str(jsonResponse) == "successful"):
            #    fo.close()
            #    remove(actual_filename)
            # mapaux = mapaux + 1
        nombre_mapas = ["fengGui_gazeplot", "fengGui_aoi", "fengGui_heatmap", "fengGui_opacity"]
        data = {"idStimulus": stimulus.id_stimulus, "api": 3, "maps": json.dumps(nombre_mapas)}

        if userCreation != None:
            # data.update({"userCreation": userCreation})
            data["userCreation"]= userCreation
        
        # fgaze = open(namesMap["gazeplot"], 'rb')
        # faoi = open(namesMap["aoi"], 'rb')
        # fopacity = open(namesMap["opacity"],'rb')
        # fheatmap = open(namesMap["heatmap"],'rb')
        archivos_enviar = {}
        for i, archivo in enumerate(namesMap):
            archivos_enviar[f'archivo{i}'] = open(namesMap[archivo], 'rb')

        #filesMap = {'gazeplot': fgaze, 'aoi': faoi, 'opacity': fopacity, 'heatmap': fheatmap}
        #filesMap = {'archivos': archivos_enviar}
        headers = {'Authorization': f'Bearer {token}'}
        url_upload = f'{BACKEND}/Stimulus/SaveAndUploadMaps'
        r = requests.post(url=url_upload, files=archivos_enviar ,data=data, headers=headers)
        jsonResponse = r.json()

        print(jsonResponse)

        if (str(jsonResponse) == "successful"):
            for ar in archivos_enviar.values():
                ar.close()
            # fgaze.close()
            # faoi.close()
            # fopacity.close()
            # fheatmap.close()
            remove(namesMap["gazeplot"])
            remove(namesMap["aoi"])
            remove(namesMap["opacity"])
            remove(namesMap["heatmap"])

            
        #Guardar los scores
        #pasar a una funcion aparte de obtener metricas
        data = {'api': Apis.FENGUI.value} #identificar que el 3 es la metrica de feng

        headers = {'Authorization': f'Bearer {token}'}

        url_metrics = f'{BACKEND}/Stimulus/getApiMetrics'
        ApiMetrics = requests.post(url=url_metrics ,data=data, headers=headers)
        ApiMetrics = json.loads(ApiMetrics.text)

        print(ApiMetrics)
        print(ApiMetrics[0]["id"])
        print(len(ApiMetrics))

        ApiMetrics.append({"name":"cognitive_load", "id":1}) 
        ApiMetrics.append({"name":"clarity", "id":2}) 
        ApiMetrics.append({"name":"effectivity", "id":3}) 
            
        # i = 0
        clear = FengResponse['result']['clear']
        complexity = FengResponse['result']['complexity']


        #TODO: cambiar a un modelo

        focus = round(((clear + clarity)/2), 2)
        print(f'focus: {focus} clear {clear} clarity {clarity}')

        cognitive_demand = round(model.predict(np.array([[float(complexity), (100-clarity)]]))[0][0], 2)

        print(f'clear: {clear}')

        FengResponse['result']['cognitive_load'] = cognitive_demand
        FengResponse['result']['clarity'] = focus #clarity 
        FengResponse['result']['effectivity'] = round(((focus) + (100 - cognitive_demand))/2, 2)
        values = [{"value": round(float(FengResponse["result"][(metric["name"]).lower()]), 2), "id": metric["id"]}  for metric in ApiMetrics]
        # for metric in ApiMetrics:
        #     data = {"value": FengResponse["result"][(metric["name"]).lower()]
        #             , "idMetric": metric["id"]
        #             , "idStimulus": stimulus.id_stimulus}

        #     if userCreation != None:
        #         data["userCreation"]= userCreation

        #     headers = {'Authorization': f'Bearer {token}'}
        #     url_add_score = f'{BACKEND}/Stimulus/AddToScore'
        #     r = requests.post(url=url_add_score, data=data, headers=headers)
        #     jsonResponse = r.json()
        #     print(jsonResponse)
        #     if("inserted" not in(jsonResponse)):
        #         return "fail"
        #print(values)
        values_json = json.dumps(values)
        data = {"values": values_json, "idStimulus": stimulus.id_stimulus}

        if userCreation != None:
            data["userCreation"]= userCreation

        headers = {'Authorization': f'Bearer {token}'}
        url_add_score = f'{BACKEND}/Stimulus/AddAllScores'
        r = requests.post(url=url_add_score, data=data, headers=headers)
        jsonResponse = r.json()
        print(jsonResponse)
        if("inserted" not in(jsonResponse)):
            return "fail"


            #chequear si hay aois , si sí guardar
        
        if ("aOIs" in FengResponse['result']):
            aois = FengResponse['result']['aOIs']
            aois_values = [{'punctuation': float(aoi['visibilityScore']), 'name': aoi['text']} for aoi in aois]
            aois_values_json = json.dumps(aois_values)
            data = {'values': aois_values_json, 'idStimulus': stimulus.id_stimulus, 'idApi': Apis.FENGUI.value}

            if userCreation != None:
                data["userCreation"] = userCreation

            headers = {'Authorization': f'Bearer {token}'}
            r = requests.post(url=f"{BACKEND}/Stimulus/InsertAllAois",data=data, headers=headers)
            jsonResponse = r.json()

            if("inserted" not in(jsonResponse)):
                return "fail"

            # j = 0
            # for aoi in aois:

            #     data = {'punctuation': aoi['visibilityScore']
            #             , 'name': aoi['text']
            #             , 'idStimulus': stimulus.id_stimulus
            #             , 'idApi': Apis.FENGUI.value}

            #     if userCreation != None:
            #         data["userCreation"]= userCreation

            #     headers = {'Authorization': f'Bearer {token}'}
            #     # r = requests.post(url=Backend + "/Stimulus/InsertAoi",data=data, headers=headers)
            #     r = requests.post(url=f"{BACKEND}/Stimulus/InsertAoi",data=data, headers=headers)
            #     jsonResponse = r.json()

            #     if("inserted" not in(jsonResponse)):
            #         return "fail"
            #     j = j + 1


        #save size of stimulus
        #data = {'idStimulus': stimulus.id_stimulus, 'size': size}
        #headers = {'Authorization': f'Bearer {token}'}

        #url_update_size = f'{BACKEND}/Stimulus/UpdateSize'
        # size = requests.post(url=Backend + "/Stimulus/UpdateSize",data=data, headers=headers)
        #size = requests.post(url=url_update_size, data=data, headers=headers)
        

        return "Successful"
        
    return "something gone wrong"

def analyzeVids(stimulus: Stimulus, token: str, credentials:ApiCredential):
    
    jsonrpc = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "VideoAttention",
        "params": { "InputVideo" : stimulus.image_url, 
                   "viewType" : 0, 
                   "ViewDistance" : 1, 
                   "analysisOptions" : 48, 
                   "outputOptions" : 69
        }
    }
    
    headers = {'Authorization': f'Basic {credentials.clave}'}
    r = requests.post(url=credentials.url, json=jsonrpc, headers=headers)
    FengResponse = r.json()

    if ("result" in FengResponse):
        id = FengResponse['result']['imageID']
        return { "result": id, "message": "success" }

    return { "result": FengResponse, "message": "failed" }

def getAndSaveCsv(stimulus: Stimulus, token: str, credentials: ApiCredential, idvid: str):
    #Obtener csv y guardar su resultado
    headers = {'Authorization': f'Basic {credentials.clave}'}
    url_feng = f'https://service.feng-gui.com/users/erick.moreno.troiatec.com/files/images/{idvid.replace(".mp4", "_gazedata.csv")}'
    csvf = requests.get(url=url_feng, headers=headers)

    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y%m%d%H%M%S")

    csv_name = f'{formatted_time}{stimulus.title}_scores.csv'

    with open(csv_name, 'wb') as f:
        f.write(csvf.content)

    #Obtener promedios de métricas 
    columnas_interes = ['Complexity', 'Focus']

    # Diccionario para almacenar los totales de las columnas
    totales = {col: 0 for col in columnas_interes}
    # Diccionario para almacenar el conteo de las filas
    conteo_filas = {col: 0 for col in columnas_interes}

    with open(csv_name, 'r') as archivo:
        reader = csv.reader(archivo)
        header = next(reader)  # Saltar la primera fila (encabezados)
    
        # Determinar las posiciones de las columnas de interés
        posiciones_interes = [header.index(col) for col in columnas_interes]

        for fila in reader:
            #print(fila)
            for i, valor in enumerate(fila):
                if i in posiciones_interes:
                    try:
                        valor = float(valor)
                        col = header[i]
                        totales[col] += valor
                        conteo_filas[col] += 1
                    except ValueError:
                        # El valor no es numérico
                        pass    

    promedios = {col: totales[col] / conteo_filas[col] for col in columnas_interes}   
    effectivity = round((((100 - promedios["Complexity"]) + promedios["Focus"]) / 2), 2)
    
    #Enviar todo al backend para ser guardado (scores, csv)
    data =  {"idStimulus": stimulus.id_stimulus, "Complexity": round(promedios["Complexity"], 2), "Focus": round(promedios["Focus"] , 2), "Effectivity": effectivity}
    fo = open(csv_name, 'rb')
    file = {'file': fo}
    headers = {'Authorization': f'Bearer {token}'}
    url_upload = f'{BACKEND}/Stimulus/SaveAndUploadCSV'
    r = requests.post(url=url_upload, files=file ,data=data, headers=headers)
    print(r)
    jsonResponse = r.json()
    print(jsonResponse)
    if (str(jsonResponse) == "inserted"):
        fo.close()
        remove(csv_name)
        return "Successful"

def getAndSaveVids(stimulus: Stimulus, token: str, credentials: ApiCredential, idvid: str):
    size = 0
    vidsArr = ['heatmap', 'opacity']

    for vid in vidsArr:
        headers = {'Authorization': f'Basic {credentials.clave}'}
        url_feng = f'https://service.feng-gui.com/users/erick.moreno.troiatec.com/files/images/{idvid.replace(".mp4", "_" + vid + ".mp4")}'
        actvid = requests.get(url= url_feng, headers=headers)
        
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%Y%m%d%H%M%S")
            
        actual_filename = f'{formatted_time}{stimulus.title}_feng_{vid}.mp4'# + '_feng_' + mapa +'.png'
        
        with open(actual_filename, 'wb') as f:
            f.write(actvid.content)

        size+= os.path.getsize(actual_filename)
        
        data = {"idStimulus": stimulus.id_stimulus,
            "type": vid}
        
        fo = open(actual_filename, 'rb')
        file = {'file': fo}
        headers = {'Authorization': f'Bearer {token}'}
        url_upload = f'{BACKEND}/Stimulus/GetAndUploadVids'

        r = requests.post(url=url_upload, files=file ,data=data, headers=headers)
        jsonResponse = r.json()
        print(jsonResponse)
        if(str(jsonResponse) == "successful"):
            fo.close()
            remove(actual_filename)
            
    #save size of stimulus
    data = {'idStimulus': stimulus.id_stimulus, 'size': size}
    headers = {'Authorization': f'Bearer {token}'}

    url_update_size = f'{BACKEND}/Stimulus/UpdateSize'
    size = requests.post(url=url_update_size, data=data, headers=headers)

    return "Successful"

def sendMail(id: str, vidName: str, folderName: str, token: str, tipo: str):
    data = {'id': id, 'vidName': vidName, 'folderName': folderName, 'tipo': tipo}
    headers = {'Authorization': f'Bearer {token}'}
    url = f'{BACKEND}/Stimulus/AdviceVideoAnalisis'
    requests.post(url=url, data=data, headers=headers)
    return "true"

def handleStatus(idStimulus, status, token: str):
    data = {'id': idStimulus, 'status': status, 'error': ""}
    headers = {'Authorization': f'Bearer {token}'}
    url = f'{BACKEND}/Stimulus/handleStatus'
    requests.post(url=url, data=data, headers=headers)
    return "true"

