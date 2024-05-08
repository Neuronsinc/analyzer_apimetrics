from fastapi import APIRouter, File, UploadFile, Request, Form

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

BACKEND = 'https://analyzerapi.troiatec.com'
#BACKEND = 'http://localhost/Analyzer/Predict_Analyzer_Back/'

def comprimir_imagen(file):
    imagen_original = Image.open(BytesIO(file.read()))

    try:
        # Obtener información de los metadatos EXIF
        exif_info = imagen_original.getexif()
        # Buscar la etiqueta de orientación en los metadatos EXIF
        for tag, value in exif_info.items():
            if ExifTags.TAGS.get(tag) == 'Orientation':
                if value == 3:
                    # Rotar 180 grados (invertir horizontal y verticalmente)
                    imagen_original = imagen_original.rotate(180, expand=True)
                elif value == 6:
                    # Rotar 270 grados (invertir horizontal y girar 90 grados)
                    imagen_original = imagen_original.rotate(-90, expand=True)
                elif value == 8:
                    # Rotar 90 grados (invertir verticalmente y girar 90 grados)
                    imagen_original = imagen_original.rotate(90, expand=True)
                break
    except (AttributeError, KeyError, IndexError):
        # La imagen no tiene información de orientación en los metadatos EXIF
        pass
    
    return imagen_original


# @router.post("/Predict/analyze")
@router.post('/Analyzer/Stimulus')
def data(t: Request, file: UploadFile = File(...), id_folder: str = Form()):
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
            
        
        # fileName = str(today.day) + str(today.month) + str(today.year) + "_" +str(today.hour)+str(today.minute)+str(today.second) + (re.sub('[^A-Za-z0-9]+','',re.sub('\s+', '-', (originalName).lower()))) + extension
        h = f'{datetime.now().strftime("%d%m%Y_%H%M%S")}'
        # digest = h.hexdigest()
        # print(digest)
        reg = re.sub('[^A-Za-z0-9]+','',re.sub('\s+', '-', (originalName).lower()))
        fileName = f"{h}{reg}{extension}"
        
        if  (extension != ".mp4"):
            redimensionada = comprimir_imagen(file.file)
            redimensionada.save(fileName)
        else:
            with open(fileName, 'wb') as f:
                shutil.copyfileobj(file.file, f)
                #shutil.copyfileobj(redimensionada, f)

        data = {'id_folder': id_folder}
        # fo = open(RootPath + fileName, 'rb')
        fo = open(fileName, 'rb')
        ff = {'image': fo} # la ruta debe ser cambiada por la ruta del servidor
        headers = {'Authorization': token}

        r = requests.post(url=f'{BACKEND}/Stimulus/UploadStimulus', files=ff ,data=data, headers=headers)
        status_c = r.status_code
        print(r)
        print(r.content)
        jsonResponse = r.json()
        fo.close()

        if (status_c == 200):
            # remove(RootPath + fileName)
            remove(fileName)
            return {"idStimulus": str(jsonResponse)}
        else:
            remove(fileName)
            return JSONResponse(content="Error uploading the file", status_code=status_c)

        
    except Exception as ex:
        print(ex)
        raise {"message": "Error uploading the file"}
    finally:
        file.file.close()