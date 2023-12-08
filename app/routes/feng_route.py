from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from typing import List
# from app.apis.predict.predict import analyze_file
# from app.apis.predict.predict import download_file
from app.apis.predict.predict_user import UserList
from app.apis.predict import predict, driver
import shutil
from app.apis.feng.feng import analyze
from app.apis.feng.feng import get_dataset
from app.apis.feng.feng import analyzeVids, getAndSaveCsv, getAndSaveVids, sendMail, handleStatus

from app.apis.analyzer.analyzer import get_api_credentials
from app.apis.analyzer.analyzer import get_stimulus

from app.model.api_model import ARequest
from app.model.api_model import Apis
from app.model.feng_vids_model import VRequest, RedisReq
# from app.model.attention_model import StudySettings
import redis
import json

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

    credentials = get_api_credentials(Apis.FENGUI.value, arequest.analyzer_token)
    stimulus = get_stimulus(arequest.id_stimulus, arequest.analyzer_token)

    # studySettings = {"study_name": getS["title"], "study_type": "general", "content_type": "general", 'tasks[0]': 'focus', 'tasks[1]': 'clarity_score'}
    analyze(stimulus, float(arequest.clarity), arequest.analyzer_token, credentials)

    handleStatus(arequest.id_stimulus, 2, arequest.analyzer_token)

    return "ok"

@router.post('/Feng/analyze/vids')
def data(arequest: VRequest):
    credentials = get_api_credentials(Apis.FENGUI.value, arequest.analyzer_token)
    stimulus = get_stimulus(arequest.id_stimulus, arequest.analyzer_token)

    data = analyzeVids(stimulus, arequest.analyzer_token, credentials)

    if data["message"] == "success":
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
        'FolderName': arequest.FolderName
        }

        # Serializar el objeto como una cadena JSON
        cadena_json = json.dumps(mi_objeto)

        # Agregar la cadena JSON a una lista en Redis
        connection.rpush('Procesar', cadena_json)
        connection.publish('Procesar', cadena_json)
        return JSONResponse(content=data["result"], status_code=200)

    return JSONResponse(content=data["result"], status_code=500)


@router.post('/Feng/upload/vids')
def data(arequest: RedisReq):
    credentials = get_api_credentials(Apis.FENGUI.value, arequest.token)
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