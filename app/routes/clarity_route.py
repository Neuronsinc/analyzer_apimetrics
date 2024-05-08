from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from typing import List

import shutil

from app.model.clarity_model import clarity_model_manager

import json
import psutil
import os
import random
import requests
import time

router = APIRouter()

route_predict = 'app/image_cache'


@router.post("/clarity/memtest")
def memory_test(url: str):
    process = psutil.Process(os.getpid())
    memory_1 = process.memory_info().rss / (1024 * 1024)  # Convertir a MB
    print(f'antes de la prediccion: {memory_1}')
    start_time = time.time()

    if url == '':
        url = f'https://picsum.photos/id/1/2048/1600'

    img = ImageCaracteristics(url)
    x = clarity_model_manager.get_clarity_prediction(img.clarity())

    process = psutil.Process(os.getpid())
    memory_2 = process.memory_info().rss / (1024 * 1024)  # Convertir a MB
    print(f'despues de la prediccion: {memory_2}')
    tiempo = time.time() - start_time
    print("--- %s seconds ---" % (tiempo))

    return {'memory_1': memory_1, 'memory_2':memory_2, **x, "duration": tiempo }