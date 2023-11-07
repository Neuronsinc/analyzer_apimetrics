from fastapi import APIRouter, File, UploadFile, Request, Form

# from app.apis.predict.predict import analyze_file
# from app.apis.predict.predict import download_file
# from app.apis.analyzer import send_to_analyzer
import requests
import os
from os import remove
import shutil
from datetime import datetime
import re
import hashlib


router = APIRouter()

route_predict = 'app/image_cache'

BACKEND = 'https://analyzerapi.troiatec.com'
#BACKEND = 'http://localhost/Analyzer/Predict_Analyzer_Back/'


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
        
        with open(fileName, 'wb') as f:
            shutil.copyfileobj(file.file, f)

        data = {'id_folder': id_folder}
        # fo = open(RootPath + fileName, 'rb')
        fo = open(fileName, 'rb')
        ff = {'image': fo} # la ruta debe ser cambiada por la ruta del servidor
        headers = {'Authorization': token}

        r = requests.post(url=f'{BACKEND}/Stimulus/UploadStimulus', files=ff ,data=data, headers=headers)
        jsonResponse = r.json()
        fo.close()

        if ("msgError" not in str(jsonResponse)):
            # remove(RootPath + fileName)
            remove(fileName)
            return {"idStimulus": str(jsonResponse)}
        
    except Exception as ex:
        print(ex)
        raise {"message": "Error uploading the file"}
    finally:
        file.file.close()