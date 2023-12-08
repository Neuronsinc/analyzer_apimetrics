from fastapi import APIRouter, File, UploadFile
from typing import List
# from app.apis.predict.predict import analyze_file
# from app.apis.predict.predict import download_file
from app.apis.predict.predict_user import UserList
from app.apis.predict import predict, driver
import shutil
from app.apis.attention.attention import analyze
from app.apis.attention.attention import get_dataset

from app.apis.feng.feng import handleStatus

from app.apis.analyzer.analyzer import get_api_credentials
from app.apis.analyzer.analyzer import get_stimulus
from app.model.api_model import ARequest
from app.model.api_model import Apis
from app.model.attention_model import StudySettings
from fastapi.responses import JSONResponse


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

    credentials = get_api_credentials(Apis.ATTENTION.value, arequest.analyzer_token)

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

    credentials = get_api_credentials(Apis.ATTENTION.value, arequest.analyzer_token)
    get_dataset(arequest.id_stimulus, credentials=credentials, max=200)
    
    return "fff"