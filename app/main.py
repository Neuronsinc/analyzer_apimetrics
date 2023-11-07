from fastapi import FastAPI, File, UploadFile, Body
from datetime import datetime

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routes import feng_route
from app.routes import attention_route
from app.routes import predict_route
from app.routes import analyzerbot_route

# origins = [
#     "http://localhost",
#     "http://localhost:3000",
#     "https://desaanalyzer.troiatec.com/"
# ]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(feng_route.router)
app.include_router(attention_route.router)
app.include_router(predict_route.router)
app.include_router(analyzerbot_route.router)
