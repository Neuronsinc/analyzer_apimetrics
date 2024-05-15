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
def data(t: Request, file: UploadFile = File(...), id_folder: str = Form(), id_father: str = Form()):
# def data(t: Request, file: UploadFile = File(...), id_folder: str = Form()):
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
            remove(fileName)
            return {"idStimulus": str(jsonResponse), "idFolder": id_folder, "idFather": id_father}
            # return {"idStimulus": str(jsonResponse), "idFolder": id_folder}
        else:
            remove(fileName)
            return JSONResponse(content="Error uploading the file", status_code=status_c)

        
    except Exception as ex:
        print(ex)
        raise {"message": "Error uploading the file"}

    finally:
        file.file.close()