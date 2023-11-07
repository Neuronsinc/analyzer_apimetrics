from fastapi import APIRouter, File, UploadFile
import hashlib
import pymongo
import boto3
from typing import List
# from app.apis.predict.predict import analyze_file
# from app.apis.predict.predict import download_file
from app.apis.predict.predict_user import UserList
from app.apis.predict import predict, driver

from app.apis.analyzer.analyzer import get_stimulus
from app.apis.analyzer.analyzer import upload_zip
from app.apis.analyzer.analyzer import Stimulus

from app.model.api_model import ARequest

from pydantic import BaseModel

import requests

import shutil

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


router = APIRouter()

route_predict = 'app/image_cache'

@router.post("/Predict/analyzeFile")
async def analyze_file(file: UploadFile):
    try:
        filename = file.filename
        file_location = f'{route_predict}/{filename}'

        d = driver.configure_driver()
        with open(file_location, "wb+") as file_object:
            print(file_location)
            shutil.copyfileobj(file.file, file_object)

        user:User = UserList().get_user(1)
        # user:User = UserList().get_user(3)

        result_analyze = predict.analyze_file(user=user, driver=d, image=file_location)
        result_download = predict.download_file(user=user, driver=d, stimulus=filename)
        d.quit()
        return {"filename": file.filename}
    except Exception as ex:
        d.quit()
        print(ex)
        raise Exception(ex)



@router.post("/Predict/analyze")
def analyze_from_predict(arequest: ARequest):
    options = driver.driver_options()

    print("driver")

    d = webdriver.Chrome(options=options)
    d.execute_cdp_cmd("Page.setBypassCSP", {"enabled": True})
    d.maximize_window()
    try:

        print(f'POST params {arequest.analyzer_token[0:10]}, {arequest.id_stimulus}')
        stimulus:Stimulus = get_stimulus(arequest.id_stimulus, arequest.analyzer_token)
        print(stimulus)

        img_data = requests.get(stimulus.image_url).content
        with open(stimulus.filename, 'wb') as f:
            f.write(img_data)

        user:User = UserList().get_user(1)

        result_analyze = predict.analyze_file(user=user, driver=d, image=stimulus.filename)
        result_download = predict.download_file(user=user, driver=d, stimulus=stimulus.title)

        upload_zip(stimulus, token=arequest.analyzer_token)
        print("si termino bien esta shit")

        d.quit()
        return {"ok":"asdf"} #{"filename": file.filename}
    except Exception as ex:
        d.quit()
        raise Exception(ex)


@router.post("/Predict/Dataset")
def analyze_from_predict(arequest: ARequest):
    options = driver.driver_options()
    print(options)
    d = webdriver.Chrome(options=options)

    d.execute_cdp_cmd("Page.setBypassCSP", {"enabled": True})
    d.maximize_window()

    try:
        predict.generate_dataset(collection=arequest.id_stimulus, driver=d)
        d.quit()
        return {"ok":"asdf"} #{"filename": file.filename}
    except Exception as ex:
        d.quit()
        raise Exception(ex)
