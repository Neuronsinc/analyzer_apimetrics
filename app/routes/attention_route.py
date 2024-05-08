from fastapi import APIRouter, File, UploadFile
from typing import List
# from app.apis.predict.predict import analyze_file
# from app.apis.predict.predict import download_file

import shutil
import gc
#from memory_profiler import profile
from app.apis.attention.attention import analyze
from app.apis.attention.attention import get_dataset
from app.model.clarity_model import clarity_model_manager
from app.model.image_model import ImageCaracteristics

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
    print(arequest)
    stimulus = get_stimulus(arequest.id_stimulus, arequest.analyzer_token)
    
    response = ""
    try:
        img = ImageCaracteristics(stimulus.image_url)
        # clarity = clarity_model_manager.get_prediction(stimulus.image_url) #clarity engagement
        clarity = clarity_model_manager.get_clarity_prediction(img.clarity()) #clarity engagement
        print(clarity)
        if clarity is not None:
            response = {"clarity": str(clarity)}
            print(response)
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


@router.post("/Attention/Dataset/")
async def fill_dataset(arequest: ARequest):
    # feng.analyze_file()

    credentials = get_api_credentials(Apis.ATTENTION.value, arequest.analyzer_token, False)
    get_dataset(arequest.id_stimulus, credentials=credentials, max=200)
    
    return "fff"