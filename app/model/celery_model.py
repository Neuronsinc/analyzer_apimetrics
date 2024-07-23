from celery import Celery, chain
import gc
from app.model.api_model import ARequest
from app.model.api_model import Apis
from app.apis.analyzer.analyzer import get_api_credentials
from app.apis.analyzer.analyzer import get_stimulus

from app.model.image_model import ImageCaracteristics
from app.model.clarity_model import clarity_model_manager
from app.apis.feng.feng import handleStatus

from app.apis.feng.feng import analyzeVids, getAndSaveCsv, getAndSaveVids, sendMail, handleStatus
from app.apis.avisos.avisos import AvisoSoporte

from app.apis.analyzer.analyzer import get_api_credentials
from app.apis.analyzer.analyzer import get_stimulus
from app.model.cache_model import cache_manager

from app.apis.feng.feng import analyze

import redis
import json
import math


#Configuración
BROKER_URL = 'redis://localhost:6379/0'
BACKEND_URL = 'redis://localhost:6379/0'

REDIS='redis-14737.c274.us-east-1-3.ec2.cloud.redislabs.com'
REDISPORT=14737
REDISUSERNAME = 'default'
REDISPASSWORD = 'sBiMwZAb2w1jmwGDIMmi7kx941ArAGXQ'

#correr en windows celery (https://github.com/celery/celery/issues/4178#issuecomment-344176336):
#python -m celery -A app.model.celery_model worker --pool=solo -l info

celery_app = Celery(
    'apimetrics',
    broker= BROKER_URL,
    backend= BACKEND_URL
)

@celery_app.task
def caracteristicas(data: dict):
    # arequest = ARequest(
    #             id_stimulus=data["id_stimulus"],
    #             analyzer_token=data["analyzer_token"],
    #             clarity=data["clarity"]
    #             )
    # print(arequest)
    stimulus = get_stimulus(data["id_stimulus"], data["analyzer_token"])
    try:
        print('entreee a caracteristicaaaaasss')
        img = ImageCaracteristics(stimulus.image_url)
        data["clarity"] = img.clarity()
        data["StimulusName"] = stimulus.filename
        print(data)
        print(f'claridad: {img.clarity()}, claridad en dict: {data["clarity"]}')
        return data
    except:
        handleStatus(data["id_stimulus"], 3, data["analyzer_token"])
        return "failed"
    return "success"

@celery_app.task
def clarity_pred(data: dict):
    print(f'diccionario que debe venir de caracteristicas =>> {data}')
    # feng.analyze_file()
    # arequest = ARequest(
    #             id_stimulus=data["id_stimulus"],
    #             analyzer_token=data["analyzer_token"],
    #             clarity=data["clarity"]
    #             )
    # print(arequest)
    #stimulus = get_stimulus(arequest.id_stimulus, arequest.analyzer_token)
    
    response = ""
    try:
        #img = ImageCaracteristics(stimulus.image_url)
        # clarity = clarity_model_manager.get_prediction(stimulus.image_url) #clarity engagement
        clarity = clarity_model_manager.get_clarity_prediction(data["clarity"]) #clarity engagement
        print(clarity)
        if clarity is not None:
            response = {"clarity": str(clarity)}
            print(response)

            handleStatus(data["id_stimulus"], 1, data["analyzer_token"])

            connection = redis.Redis(host=REDIS, port=REDISPORT, username=REDISUSERNAME, password=REDISPASSWORD)
            mi_objeto = { 
            'idUser': data["idUser"],
            'idCompany': data["idCompany"],
            'idLicense': data["idLicense"],
            'idStimulus': data["id_stimulus"],
            'token': data["analyzer_token"],
            'idFolder': data["idFolder"],
            'FolderName': data["FolderName"],
            'StimulusName': data["StimulusName"],
            'finish': "false"
            }

            connection.lpush('AnalizadosImg', json.dumps(mi_objeto))
            connection.publish('AnalizadosImg', json.dumps(mi_objeto))
            #feng_analyze(arequest=arequest).apply_async()
            data["clarity"] = clarity
            del clarity
            gc.collect()
            return data
        else:
            del clarity
            gc.collect()
            raise Exception
    except:
        handleStatus(data["id_stimulus"], 3, data["analyzer_token"])
        return "failed"
        #return JSONResponse(content="failed", status_code=500)

    return "success"


@celery_app.task
def feng_analyze(data: dict):
    print(f'diccionario que debe venir de predicciones =>> {data}')
    cache = cache_manager.get_cache_instance()
    credentials = get_api_credentials(Apis.FENGUI.value, data["analyzer_token"], True, 0, cache)
    stimulus = get_stimulus(data["id_stimulus"], data["analyzer_token"])

    if credentials == "Ninguno" or credentials == "NingunaEspecifica":
        mensaje = ""
        if credentials == "Ninguno":
            mensaje = "Se acabaron los créditos en todas las cuentas y no es posible analizar nada más."
        elif credentials == "NingunaEspecifica":
            mensaje = "En ninguna cuenta hay disponibilidad para subir el estímulo requerido."

        AvisoSoporte(0, stimulus.id_folder, stimulus.filename, data["analyzer_token"], mensaje, "Todas", "Feng", stimulus.image_url)
        handleStatus(data["id_stimulus"], 3, data["analyzer_token"])
        return "failed"

    # studySettings = {"study_name": getS["title"], "study_type": "general", "content_type": "general", 'tasks[0]': 'focus', 'tasks[1]': 'clarity_score'}
    response = ""
    #model = model_manager.get_model_instance()
    #scaler = model_manager.scaler()
    try:
        response = analyze(stimulus, float(data["clarity"]), data["analyzer_token"], credentials)

        if "Successful" in response:
            
            handleStatus(data["id_stimulus"], 2, data["analyzer_token"])

            connection = redis.Redis(host=REDIS, port=REDISPORT, username=REDISUSERNAME, password=REDISPASSWORD)
            mi_objeto = { 
            'idUser': data["idUser"],
            'idCompany': data["idCompany"],
            'idLicense': data["idLicense"],
            'idStimulus': data["id_stimulus"],
            'token': data["analyzer_token"],
            'idFolder': data["idFolder"],
            'FolderName': data["FolderName"],
            'StimulusName': data["StimulusName"],
            'finish': "true"
            }

            connection.lpush('AnalizadosImg', json.dumps(mi_objeto))
            connection.publish('AnalizadosImg', json.dumps(mi_objeto))
        else:
            handleStatus(data["id_stimulus"], 3, data["analyzer_token"]) # fallo
            return "failed"
    except:
        handleStatus(data["id_stimulus"], 3, data["analyzer_token"]) # fallo
        return "failed"

    return "success"

# Procesar videos
@celery_app.task
def procesar_video(data: dict):

    cache = cache_manager.get_cache_instance()
    credentials = get_api_credentials(Apis.FENGUI.value, data["analyzer_token"], True, 1, cache, data["Duration"])
    stimulus = get_stimulus(data["id_stimulus"], data["analyzer_token"])

    if credentials == "Ninguno" or credentials == "NingunaEspecifica":
        mensaje = ""
        if credentials == "Ninguno":
            mensaje = "Se acabaron los créditos en todas las cuentas y no es posible analizar nada más."
        elif credentials == "NingunaEspecifica":
            mensaje = "En ninguna cuenta hay disponibilidad para subir el estímulo requerido."

        AvisoSoporte(0, stimulus.id_folder, stimulus.filename, data["analyzer_token"], mensaje, "Todas", "Feng", stimulus.image_url)
        handleStatus(data["id_stimulus"], 3, data["analyzer_token"])
        return 'failed'

    data_v = analyzeVids(stimulus, data["analyzer_token"], credentials)

    if data_v["message"] == "success":
        # al ser exitoso debemos restar los créditos de la cuenta seleccionada
        total_creditos_videos = math.floor(int(data["Duration"]) / 10)

        if total_creditos_videos == 0:
            total_creditos_videos = 1

        cache_manager.extract_credits(credentials.name, total_creditos_videos)

        connection = redis.Redis(host=REDIS, port=REDISPORT, username=REDISUSERNAME, password=REDISPASSWORD)
        # Objeto Python a  almacenar en Redis
        mi_objeto = {
        'videoID': data_v["result"], 
        'idUser': data["idUser"],
        'idCompany': data["idCompany"],
        'idLicense': data["idLicense"],
        'idStimulus': data["id_stimulus"],
        'token': data["analyzer_token"],
        'idFolder': data["idFolder"],
        'StimulusName': data["StimulusName"],
        'FolderName': data["FolderName"],
        'UploadedAccount': credentials.name,
        'Duration': data["Duration"]
        }

        # Serializar el objeto como una cadena JSON
        cadena_json = json.dumps(mi_objeto)

        # Agregar la cadena JSON a una lista en Redis
        connection.rpush('Procesar', cadena_json)
        connection.publish('Procesar', cadena_json)

        return 'success'
        #return JSONResponse(content=data_v["result"], status_code=200)
    
    handleStatus(data["id_stimulus"], 3, data["analyzer_token"])
    return 'failed'
    #return JSONResponse(content=data_v["result"], status_code=500)

#workflow imagenes (Caracteristicas -> prediccion -> Feng)

def pipeline(data: dict):
    chain(
        caracteristicas.s(data).set(queue='caracteristicas') |
        clarity_pred.s().set(queue='prediccion') |
        feng_analyze.s().set(queue='feng')
    ).apply_async()