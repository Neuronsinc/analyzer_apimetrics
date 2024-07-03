from fastapi import APIRouter, File, UploadFile, Request, Form, BackgroundTasks
from app.model.api_model import ARequest
from app.model.celery_model import pipeline, caracteristicas
import requests
import os
from os import remove
import shutil
from datetime import datetime
import re
import hashlib
from PIL import Image, ExifTags
from io import BytesIO
from fastapi.responses import JSONResponse


router = APIRouter()

route_predict = 'app/image_cache'

BACKEND = 'https://analyzerapiv3.troiatec.com'

def comprimir_imagen(file):
    imagen_original = Image.open(BytesIO(file.read()))

    try:
        exif_info = imagen_original.getexif()
        for tag, value in exif_info.items():
            if ExifTags.TAGS.get(tag) == 'Orientation':
                if value == 3:
                    imagen_original = imagen_original.rotate(180, expand=True)
                elif value == 6:
                    imagen_original = imagen_original.rotate(-90, expand=True)
                elif value == 8:
                    imagen_original = imagen_original.rotate(90, expand=True)
                break
    except (AttributeError, KeyError, IndexError):
        pass
    
    return imagen_original


@router.post('/Analyzer/Stimulus')
def data(background_tasks: BackgroundTasks, t: Request, file: UploadFile = File(...), id_folder: str = Form(), idUser: str = Form(), idCompany: str = Form(), idLicense: str = Form(), FolderName: str = Form()):
    token = t.headers.get('Authorization')
    print(f'id_folder {id_folder}')

    try:
        today = datetime.now()
        originalName = file.filename
        extension = ''
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
            
        
        h = f'{datetime.now().strftime("%d%m%Y_%H%M%S")}'
        reg = re.sub('[^A-Za-z0-9]+','',re.sub('\s+', '-', (originalName).lower()))
        fileName = f"{h}{reg}{extension}"
        
        if  (extension != ".mp4"):
            redimensionada = comprimir_imagen(file.file)
            redimensionada.save(fileName)
        else:
            with open(fileName, 'wb') as f:
                shutil.copyfileobj(file.file, f)

        data = {'id_folder': id_folder}
        fo = open(fileName, 'rb')
        ff = {'image': fo} 
        headers = {'Authorization': token}

        r = requests.post(url=f'{BACKEND}/Stimulus/UploadStimulus', files=ff ,data=data, headers=headers)
        status_c = r.status_code

        jsonResponse = r.json()
        fo.close()

        if (status_c == 200):
            if extension != ".mp4":
                data = {
                    "id_stimulus": str(jsonResponse),
                    "analyzer_token":token,
                    "clarity":"",
                    "idUser":idUser,
                    "idCompany":idCompany,
                    "idLicense":idLicense,
                    "idFolder": id_folder,
                    "FolderName":FolderName
                }
                #caracteristicas.apply_async(args=[data.dict()], queue='caracteristicas')
                pipeline(data)
            remove(fileName)
            return {"idStimulus": str(jsonResponse), "idFolder": id_folder}
        else:
            remove(fileName)
            return JSONResponse(content="Error uploading the file", status_code=status_c)

        
    except Exception as ex:
        print(ex)
        raise {"message": "Error uploading the file"}

    finally:
        file.file.close()

# ----------------------------------------- pruebas abajo ------------------------------------------------------
from app.model.image_model import ImageCaracteristics
from app.model.clarity_model import clarity_model_manager
import pandas as pd
import gc

def N_results():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'score.csv')
    df = pd.read_csv(file_path, sep=',')
    N = [1, 4, 8, 'size', 'dimensions']
    df_nuevo = {
        'id': [],
        'imageUrl': [],
        'title': [],
        'size': [],
        'alto': [],
        'ancho': [],
        'clarity': [],
        'N1': [],
        'N4': [],
        'N8': [],
        'Nsize': [],
        'Ndimensions': []
    }
    for index, row in df.iterrows():
        print("-----------df nuevo---------------")
        print(df_nuevo)
        print("---------------------------")
        df_nuevo['id'].append(row['id'])
        df_nuevo['imageUrl'].append(row['imageUrl'])
        df_nuevo['title'].append(row['title'])
        df_nuevo['clarity'].append(row['clarity'])
        size = 0
        alto = 0
        ancho = 0
        for n in N:
            response = ""
            try:
                img = ImageCaracteristics(row["imageUrl"], n)
                # clarity = clarity_model_manager.get_prediction(stimulus.image_url) #clarity engagement
                clarity = clarity_model_manager.get_clarity_prediction(img.clarity()) #clarity engagement
                print(clarity)
                if clarity is not None:
                    response = {"clarity": str(clarity)}
                    print(response)
                    #handleStatus(arequest.id_stimulus, 1, arequest.analyzer_token)

                    if n == 1 :
                        df_nuevo['N1'].append(clarity)
                    elif n == 4:
                        df_nuevo['N4'].append(clarity)
                    elif n == 8:
                        df_nuevo['N8'].append(clarity)
                    elif n == 'size':
                        df_nuevo['Nsize'].append(clarity)
                    elif n == 'dimensions':
                        df_nuevo['Ndimensions'].append(clarity)

                    size, alto, ancho = img.get_meta_datos()
                    del clarity
                    gc.collect()
                else:

                    if n == 1 :
                        df_nuevo['N1'].append(None)
                    elif n == 4:
                        df_nuevo['N4'].append(None)
                    elif n == 8:
                        df_nuevo['N8'].append(None)
                    elif n == 'size':
                        df_nuevo['Nsize'].append(None)
                    elif n == 'dimensions':
                        df_nuevo['Ndimensions'].append(None)

                    del clarity
                    gc.collect()
                    raise Exception
            except:
                if n == 1 :
                    df_nuevo['N1'].append(None)
                elif n == 4:
                    df_nuevo['N4'].append(None)
                elif n == 8:
                    df_nuevo['N8'].append(None)
                elif n == 'size':
                    df_nuevo['Nsize'].append(None)
                elif n == 'dimensions':
                    df_nuevo['Ndimensions'].append(None)

                #handleStatus(arequest.id_stimulus, 3, arequest.analyzer_token)
                #return JSONResponse(content="failed", status_code=500)
        df_nuevo['size'].append(size)
        df_nuevo['alto'].append(alto)
        df_nuevo['ancho'].append(ancho)

    df_nuevo = pd.DataFrame(df_nuevo, columns=['id', 'imageUrl', 'title','size', 'alto', 'ancho', 'clarity','N1','N4','N8','Nsize','Ndimensions'])
    df_nuevo.to_csv('Nresults_csv', index=False)
    pass

@router.post('/Analyzer/test')
def data(data: dict, background_tasks: BackgroundTasks):
    #pipeline(data)
    #caracteristicas.apply_async(args=[data], queue='caracteristicas')
    # ----- aparte ------

    #stimulus = get_stimulus(arequest.id_stimulus, arequest.analyzer_token)

    background_tasks.add_task(N_results())
    return "si"
    #return JSONResponse(content=response, status_code=200)


