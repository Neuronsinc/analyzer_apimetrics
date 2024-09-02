from fastapi import FastAPI, File, UploadFile, Body
from datetime import datetime

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routes import feng_route
from app.routes import attention_route
from app.routes import analyzerbot_route
from app.routes import clarity_route
from app.routes import engagement_route
from app.routes import openai_route


# from app.model.clarity_model import clarity_model_manager
# from app.model.engagement_model import engagement_model_manager

from app.model.image_model import ImageCaracteristics

import json
import psutil
import os
import random
import requests
import time


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/memtest")
def model_memtest(url: str):
    process = psutil.Process(os.getpid())
    memory_1 = process.memory_info().rss / (1024 * 1024)  # Convertir a MB
    print(f'antes de la prediccion: {memory_1}')
    start_time = time.time()

    if url == '':
        url = f'https://picsum.photos/id/1/2048/1600'

    img = ImageCaracteristics(url)
    #x = clarity_model_manager.get_clarity_prediction(img.clarity())
    #y = engagement_model_manager.get_prediction(img.engagement())

    process = psutil.Process(os.getpid())
    memory_2 = process.memory_info().rss / (1024 * 1024)  # Convertir a MB
    print(f'despues de la prediccion: {memory_2}')
    tiempo = time.time() - start_time
    print("--- %s seconds ---" % (tiempo))

    return {'memory_1': memory_1, 'memory_2':memory_2, "duration": tiempo, "clarity": x, "engagement": y}



app.include_router(feng_route.router)
app.include_router(attention_route.router)
app.include_router(analyzerbot_route.router)
app.include_router(clarity_route.router)
app.include_router(engagement_route.router)
app.include_router(openai_route.router)