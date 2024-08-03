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
import pprint

import os

BROKER_URL = os.getenv('REDIS_BROKER_URL')
BACKEND_URL = os.getenv('REDIS_BACKEND_URL')

connection = redis.Redis.from_url(os.getenv('REDIS_URL'))


celery_app = Celery(
    'apimetrics',
    broker= BROKER_URL,
    backend= BACKEND_URL
)

def messagesRedis(message: dict, type: int, status: int):
    """
    Encola mensajes de éxito o fallo en colas de Redis.

    Parameters:
    ----------
    message : dict
        El mensaje que se va a encolar.
    type : int
        El tipo de mensaje. Puede ser:
        - 0 -> imagen
        - 1 -> video
    status : int
        El estado del mensaje. Puede ser:
        - 0 -> Exitoso
        - 1 -> Fallido
    """
    if (type == 0):
        if (status == 0):
            connection.lpush('AnalizadosImg', json.dumps(message))
            connection.publish('AnalizadosImg', json.dumps(message))
        else:
            connection.lpush('FalladosImg', json.dumps(message))
            connection.publish('FalladosImg', json.dumps(message))
    else:
        if (status == 0):
            connection.rpush('Procesar', json.dumps(message))
            connection.publish('Procesar', json.dumps(message))
        else:
            connection.lpush('Fallados', json.dumps(message))
            connection.publish('Fallados', json.dumps(message))


@celery_app.task()
def error_handler(request, exc, traceback):
    task = request.task
    task_name = task[task.rfind('.') + 1:len(task)]
    data = request.args[0]
    data_pp = pprint.pformat(data,  depth=2, width=40, indent=2)

    print("=================================== AQUI EL FALLO =================================")
    print('Task "{0}" raised exception: {1!r} \n with following args: {2} \n {3}'.format(task_name, exc, data_pp, traceback))

    handleStatus(data.get("id_stimulus", ''), 3, data.get("analyzer_token", ''))

    mi_objeto = {
        'idUser': data.get("idUser", ''),
        'idCompany': data.get("idCompany", ''),
        'idLicense': data.get("idLicense", ''),
        'idStimulus': data.get("id_stimulus", ''),
        'token': data.get("analyzer_token", ''),
        'idFolder': data.get("idFolder", ''),
        'FolderName': data.get("FolderName", ''),
        'StimulusName': data.get("StimulusName", ''),
        'finish': "true" if 'feng' in task_name else "false"
    }

    messagesRedis(mi_objeto, 0, 1)


@celery_app.task
def caracteristicas(data: dict):
    # arequest = ARequest(
    #             id_stimulus=data["id_stimulus"],
    #             analyzer_token=data["analyzer_token"],
    #             clarity=data["clarity"]
    #             )
    # print(arequest)
    stimulus = get_stimulus(data["id_stimulus"], data["analyzer_token"])
    img = ImageCaracteristics(stimulus.image_url)
    lst_caracteristicas = list(map(lambda l: float(l) ,img.clarity()))
    data["clarity"] = lst_caracteristicas
    data["StimulusName"] = stimulus.filename


    return data

@celery_app.task
def clarity_pred(data: dict):
    # feng.analyze_file()
    # arequest = ARequest(
    #             id_stimulus=data["id_stimulus"],
    #             analyzer_token=data["analyzer_token"],
    #             clarity=data["clarity"]
    #             )
    # print(arequest)
    #stimulus = get_stimulus(arequest.id_stimulus, arequest.analyzer_token)

    response = ""
    #img = ImageCaracteristics(stimulus.image_url)
    # clarity = clarity_model_manager.get_prediction(stimulus.image_url) #clarity engagement
    clarity = clarity_model_manager.get_clarity_prediction(data["clarity"]) #clarity engagement
    # print(clarity)
    if clarity is not None:

        handleStatus(data["id_stimulus"], 1, data["analyzer_token"])

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

        messagesRedis(mi_objeto, 0, 0)

        #feng_analyze(arequest=arequest).apply_async()
        data["clarity"] = clarity
        del clarity
        gc.collect()
        return data
    else:
        del clarity
        gc.collect()
        raise Exception("Something gone wrong analyzing your image by extracting clarity")

@celery_app.task
def feng_analyze(data: dict):
    print(f'se inicio el proceso de Feng {data}')
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

    # response = ""
    studySettings = {"study_name": stimulus.title, "study_type": "general", "content_type": "general", 'tasks[0]': 'focus', 'tasks[1]': 'clarity_score'}
    response = analyze(stimulus, float(data["clarity"]), data["analyzer_token"], credentials)

    if "Successful" in response:

        handleStatus(data["id_stimulus"], 2, data["analyzer_token"])

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

        messagesRedis(mi_objeto, 0, 0)

    else:
        raise Exception("Something gone wrong analyzing your image with Feng")

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
        'Duration': data["Duration"],
        'idUserAnalyzer': data["idUserAnalyzer"]
        }

        messagesRedis(mi_objeto, 1, 0)

        return 'success'
        #return JSONResponse(content=data_v["result"], status_code=200)

    handleStatus(data["id_stimulus"], 3, data["analyzer_token"])

    mi_objeto = {
        'videoID': data_v.get("result", ''),
        'idUser': data["idUser"],
        'idCompany': data["idCompany"],
        'idLicense': data["idLicense"],
        'idStimulus': data["id_stimulus"],
        'token': data["analyzer_token"],
        'idFolder': data["idFolder"],
        'StimulusName': data["StimulusName"],
        'FolderName': data["FolderName"],
        'UploadedAccount': credentials.name,
        'Duration': data["Duration"],
        'idUserAnalyzer': data["idUserAnalyzer"]
    }

    messagesRedis(mi_objeto, 1, 1)

    return 'failed'
    #return JSONResponse(content=data_v["result"], status_code=500)

# def on_raw_message(body):
#     print("====================AQUI EL BODY==========================")
#     print(body)

#workflow imagenes (Caracteristicas -> prediccion -> Feng)

if (os.getenv('WITH_FENG') == 'true'):
    print("se inicializo el pipeline con feng")
    def pipeline(data: dict):
        chain(
            caracteristicas.s(data).set(queue=f'caracteristicas-{os.getenv('ENVIRONMENT')}') |
            clarity_pred.s().set(queue=f'prediccion-{os.getenv('ENVIRONMENT')}'),
            feng_analyze.s().set(queue=f'feng-{os.getenv('ENVIRONMENT')}')
        ).apply_async(link_error=error_handler.s())
else:
    print("se inicializo el pipeline sin feng")
    def pipeline(data: dict):
        chain(
            caracteristicas.s(data).set(queue=f'caracteristicas-{os.getenv('ENVIRONMENT')}') |
            clarity_pred.s().set(queue=f'prediccion-{os.getenv('ENVIRONMENT')}'),
        ).apply_async(link_error=error_handler.s())
