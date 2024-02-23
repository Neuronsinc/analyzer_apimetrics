from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from typing import List
# from app.apis.predict.predict import analyze_file
# from app.apis.predict.predict import download_file

import shutil
from app.apis.feng.feng import analyze
from app.apis.feng.feng import get_dataset
from app.apis.feng.feng import analyzeVids, getAndSaveCsv, getAndSaveVids, sendMail, handleStatus
from app.apis.avisos.avisos import AvisoSoporte

from app.apis.analyzer.analyzer import get_api_credentials
from app.apis.analyzer.analyzer import get_stimulus
from keras.models import load_model

from app.model.api_model import ARequest
from app.model.api_model import Apis
from app.model.feng_vids_model import VRequest, RedisReq

from app.model.cache_model import cache_manager
from app.model.clarity_model import model_manager

# from app.model.attention_model import StudySettings
import redis
import json
import math

router = APIRouter()

route_predict = 'app/image_cache'

REDIS='redis-14737.c274.us-east-1-3.ec2.cloud.redislabs.com'
REDISPORT=14737
REDISUSERNAME = 'default'
REDISPASSWORD = 'sBiMwZAb2w1jmwGDIMmi7kx941ArAGXQ'

@router.post("/Attention/file/analyze")
async def analyze_file(file: UploadFile):
    # feng.analyze_file()
    print("mierda")
    return "otra mierda"
    
@router.post("/Feng/Dataset/")
async def analyze_file(arequest: ARequest):
    # feng.analyze_file()
    credentials = get_api_credentials(Apis.FENGUI.value, arequest.analyzer_token)
    get_dataset(arequest.id_stimulus, credentials=credentials, max=10)
    
    return "fff"




@router.post("/Feng/analyze")
def analyze_from_predict(arequest: ARequest):
    cache = cache_manager.get_cache_instance()
    credentials = get_api_credentials(Apis.FENGUI.value, arequest.analyzer_token, True, 0, cache)
    stimulus = get_stimulus(arequest.id_stimulus, arequest.analyzer_token)

    if credentials == "Ninguno" or credentials == "NingunaEspecifica":
        mensaje = ""
        if credentials == "Ninguno":
            mensaje = "Se acabaron los créditos en todas las cuentas y no es posible analizar nada más."
        elif credentials == "NingunaEspecifica":
            mensaje = "En ninguna cuenta hay disponibilidad para subir el estímulo requerido."

        AvisoSoporte(0, stimulus.id_folder, stimulus.filename, arequest.analyzer_token, mensaje, "Todas", "Feng", stimulus.image_url)
        handleStatus(arequest.id_stimulus, 3, arequest.analyzer_token)
        return JSONResponse(content="failed", status_code=500)

    # studySettings = {"study_name": getS["title"], "study_type": "general", "content_type": "general", 'tasks[0]': 'focus', 'tasks[1]': 'clarity_score'}
    response = ""
    model = model_manager.get_model_instance()
    try:
        response = analyze(stimulus, float(arequest.clarity), arequest.analyzer_token, credentials, model)
        # al ser exitoso debemos restar los créditos de la cuenta seleccionada
        cache_manager.extract_credits(credentials.name, 1)

        handleStatus(arequest.id_stimulus, 2, arequest.analyzer_token)
    except:
        handleStatus(arequest.id_stimulus, 3, arequest.analyzer_token) # fallo
        return JSONResponse(content="failed", status_code=500)

    return JSONResponse(content=response, status_code=200)



@router.post('/Feng/analyze/vids')
def data(arequest: VRequest):
    cache = cache_manager.get_cache_instance()
    credentials = get_api_credentials(Apis.FENGUI.value, arequest.analyzer_token, True, 1, cache, arequest.Duration)
    stimulus = get_stimulus(arequest.id_stimulus, arequest.analyzer_token)

    if credentials == "Ninguno" or credentials == "NingunaEspecifica":
        mensaje = ""
        if credentials == "Ninguno":
            mensaje = "Se acabaron los créditos en todas las cuentas y no es posible analizar nada más."
        elif credentials == "NingunaEspecifica":
            mensaje = "En ninguna cuenta hay disponibilidad para subir el estímulo requerido."

        AvisoSoporte(0, stimulus.id_folder, stimulus.filename, arequest.analyzer_token, mensaje, "Todas", "Feng", stimulus.image_url)
        handleStatus(arequest.id_stimulus, 3, arequest.analyzer_token)
        return JSONResponse(content="failed", status_code=500)

    data = analyzeVids(stimulus, arequest.analyzer_token, credentials)

    if data["message"] == "success":
        # al ser exitoso debemos restar los créditos de la cuenta seleccionada
        total_creditos_videos = math.floor(int(arequest.Duration) / 10)

        if total_creditos_videos == 0:
            total_creditos_videos = 1

        cache_manager.extract_credits(credentials.name, total_creditos_videos)
        
        connection = redis.Redis(host=REDIS, port=REDISPORT, username=REDISUSERNAME, password=REDISPASSWORD)
        # Objeto Python a  almacenar en Redis
        mi_objeto = {
        'videoID': data["result"], 
        'idUser': arequest.idUser,
        'idCompany': arequest.idCompany,
        'idLicense': arequest.idLicense,
        'idStimulus': arequest.id_stimulus,
        'token': arequest.analyzer_token,
        'idFolder': arequest.idFolder,
        'StimulusName': arequest.StimulusName,
        'FolderName': arequest.FolderName,
        'UploadedAccount': credentials.name,
        'Duration': arequest.Duration
        }

        # Serializar el objeto como una cadena JSON
        cadena_json = json.dumps(mi_objeto)

        # Agregar la cadena JSON a una lista en Redis
        connection.rpush('Procesar', cadena_json)
        connection.publish('Procesar', cadena_json)
        return JSONResponse(content=data["result"], status_code=200)
    
    handleStatus(arequest.id_stimulus, 3, arequest.analyzer_token)
    return JSONResponse(content=data["result"], status_code=500)


@router.post('/Feng/upload/vids')
def data(arequest: RedisReq):
    cache = cache_manager.get_cache_instance()
    credentials = get_api_credentials(Apis.FENGUI.value, arequest.token, False, 1, cache, 1, arequest.UploadedAccount)
    stimulus = get_stimulus(arequest.idStimulus, arequest.token)

    csv = getAndSaveCsv(stimulus, arequest.token, credentials, arequest.videoID)
    vids = getAndSaveVids(stimulus, arequest.token, credentials, arequest.videoID)

    if (csv == "Successful" and vids == "Successful"):
        connection = redis.Redis(host=REDIS, port=REDISPORT, username=REDISUSERNAME, password=REDISPASSWORD)

        mi_objeto = {
        'videoID': arequest.videoID, 
        'idUser': arequest.idUser,
        'idCompany': arequest.idCompany,
        'idLicense': arequest.idLicense,
        'idStimulus': arequest.idStimulus,
        'token': arequest.token,
        'idFolder': arequest.idFolder,
        'StimulusName': arequest.StimulusName,
        'FolderName': arequest.FolderName
        }
        handleStatus(mi_objeto["idStimulus"], 2, mi_objeto['token'])
        connection.lpush('Analizados', json.dumps(mi_objeto))
        connection.publish('Analizados', json.dumps(mi_objeto))
        sendMail(mi_objeto['idUser'], mi_objeto['StimulusName'], mi_objeto['FolderName'], mi_objeto['token'], "0")
    else:
        connection = redis.Redis(host=REDIS, port=REDISPORT, username=REDISUSERNAME, password=REDISPASSWORD)

        mi_objeto = {
        'videoID': arequest.videoID, 
        'idUser': arequest.idUser,
        'idCompany': arequest.idCompany,
        'idLicense': arequest.idLicense,
        'idStimulus': arequest.idStimulus,
        'token': arequest.token,
        'idFolder': arequest.idFolder,
        'StimulusName': arequest.StimulusName,
        'FolderName': arequest.FolderName
        }
        handleStatus(mi_objeto["idStimulus"], 3, mi_objeto['token'])
        connection.lpush('Fallados', json.dumps(mi_objeto))
        connection.publish('Fallados', json.dumps(mi_objeto))
        sendMail(mi_objeto['idUser'], mi_objeto['StimulusName'], mi_objeto['FolderName'], mi_objeto['token'], "1")
    
    return "ok"