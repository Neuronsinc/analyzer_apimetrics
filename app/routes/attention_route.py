from fastapi import APIRouter, File, UploadFile
from typing import List
# from app.apis.predict.predict import analyze_file
# from app.apis.predict.predict import download_file

import shutil
import gc
#from memory_profiler import profile
from app.apis.attention.attention import analyze
from app.apis.attention.attention import get_dataset
from app.model.clarity_model import model_manager

from app.apis.feng.feng import handleStatus

from app.apis.analyzer.analyzer import get_api_credentials
from app.apis.analyzer.analyzer import get_stimulus
from app.model.api_model import ARequest
from app.model.api_model import Apis
from app.model.attention_model import StudySettings
from fastapi.responses import JSONResponse

#import psutil

router = APIRouter()

route_predict = 'app/image_cache'

@router.post("/Attention/file/analyze")
async def analyze_file(file: UploadFile):
    # feng.analyze_file()
    print("mierda")
    return "otra mierda"
    

@router.post("/Attention/analyze")
def analyze_from_predict(arequest: ARequest):
    # feng.analyze_file()

    credentials = get_api_credentials(Apis.ATTENTION.value, arequest.analyzer_token, False, 0)

    stimulus = get_stimulus(arequest.id_stimulus, arequest.analyzer_token)
    settings = StudySettings(study_name=stimulus.title, study_type='general', content_type='general')

    response = ""
    try:
        response = analyze(stimulus, arequest.analyzer_token, credentials, settings)
        handleStatus(arequest.id_stimulus, 1, arequest.analyzer_token)
    except:
        handleStatus(arequest.id_stimulus, 3, arequest.analyzer_token)
        return JSONResponse(content="failed", status_code=500)

    return JSONResponse(content=response, status_code=200)


@router.post("/Attention/analyze2")
#@profile
def analyze_from_predict(arequest: ARequest):
    # feng.analyze_file()
    stimulus = get_stimulus(arequest.id_stimulus, arequest.analyzer_token)
    
    response = ""
    try:
        clarity = model_manager.get_prediction(stimulus.image_url)
        if clarity is not None:
            response = {"clarity": str(clarity)}
            handleStatus(arequest.id_stimulus, 1, arequest.analyzer_token)
            del clarity
            gc.collect()
        else:
            del clarity
            gc.collect()
            raise Exception
    except:
        handleStatus(arequest.id_stimulus, 3, arequest.analyzer_token)
        return JSONResponse(content="failed", status_code=500)

    return JSONResponse(content=response, status_code=200)


# @router.post("/Attention/Memory")
# def memory():
#         # Obtener el PID (Identificador de Proceso) del proceso actual
#     pid = psutil.Process()

#     # Obtener el uso de memoria actual en bytes
#     memoria_actual = pid.memory_info().rss

#     # Convertir bytes a megabytes para una mejor legibilidad
#     memoria_mb = memoria_actual / (1024 * 1024)

#     print(f"Uso actual de memoria RAM: {memoria_mb:.2f} MB")


# @router.post("/Attention/Dataset")
# def analyze_from_predict(arequest: ARequest):

#     credentials = get_api_credentials(Apis.ATTENTION.value, arequest.analyzer_token)

#     stimulus = get_stimulus(arequest.id_stimulus, arequest.analyzer_token)
#     settings = StudySettings(study_name=stimulus.title, study_type='general', content_type='general')

#     analyze(stimulus, arequest.analyzer_token, credentials, settings)

#     return "ok"

@router.post("/Attention/Dataset/")
async def fill_dataset(arequest: ARequest):
    # feng.analyze_file()

    credentials = get_api_credentials(Apis.ATTENTION.value, arequest.analyzer_token, False)
    get_dataset(arequest.id_stimulus, credentials=credentials, max=200)
    
    return "fff"