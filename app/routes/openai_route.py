import re
from app.model.recommendation_model import Interpretations, Recommendation, StimulusRecommendations
from app.model.recommendation_request_model import RecommendationRequest
from fastapi import FastAPI, HTTPException, APIRouter, Request
import os
import requests
import pymongo
from bson import ObjectId
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv("app/.env", override=False)

mongo_url = os.environ.get("MONGO_URL")
router = APIRouter()
pymongo_client = pymongo.MongoClient(mongo_url)

# Configuración del orquestador n8n
N8N_WEBHOOK_URL = "https://n8n.troiatec.com/webhook-test/582094c9-1ff8-4657-a43e-251336b47f83"

@router.post("/recommendation/")
async def generate_recommendations(stimulus: RecommendationRequest, request: Request):
    """
    Recibe la petición del frontend, crea el registro en Mongo y delega a n8n.
    """
    recommendations_collection = pymongo_client.get_database("analyzer").get_collection("recommendations")
    
    # Extraemos el token original por si n8n necesita validar permisos
    auth_header = request.headers.get("authorization")

    # Estructura inicial del documento
    initial_doc = {
        "stimulus_id": stimulus.stimulus_id,
        "folder_id": stimulus.folder_id,
        "recommendations": [],
        "interpretations": {
            "heat_map_es": None, "heat_map_en": None,
            "gaze_plot_es": None, "gaze_plot_en": None,
            "focus_map_es": None, "focus_map_en": None,
            "aois_es": None, "aois_en": None
        },
        "conclusion_en": "",
        "conclusion_es": "",
        "image_url": stimulus.image_url,
        "benchmark": stimulus.benchmark,
        "status": 3, # Estado: Procesando (activa el spinner en React)
    }

    try:
        # 1. Insertar en MongoDB para que el sistema sepa que empezó el proceso
        inserted_result = recommendations_collection.insert_one(initial_doc)
        inserted_id = str(inserted_result.inserted_id)

        # 2. Preparar el paquete para n8n
        # Enviamos todo el JSON del frontend + el ID de la base de datos para que n8n sepa qué actualizar al final
        payload = stimulus.dict()
        payload["mongo_insertion_id"] = inserted_id 

        # 3. Disparar el Webhook de n8n
        headers = {"Authorization": auth_header} if auth_header else {}
        
        try:
            # Enviamos el POST y no esperamos a que termine (timeout corto de conexión)
            n8n_response = requests.post(
                N8N_WEBHOOK_URL, 
                json=payload, 
                headers=headers,
                timeout=5 
            )
            
            return {
                "status": "forwarded_to_n8n",
                "mongo_id": inserted_id,
                "n8n_status": n8n_response.status_code,
                "message": "Petición delegada al flujo de n8n exitosamente."
            }

        except requests.exceptions.RequestException as e:
            print(f"--- FALLO DE CONEXIÓN CON N8N --- {str(e)}")
            # Si n8n está caído, marcamos el error en la DB
            recommendations_collection.update_one(
                {"_id": ObjectId(inserted_id)},
                {"$set": {"status": 5}}
            )
            raise HTTPException(status_code=502, detail="El orquestador n8n no está respondiendo.")

    except Exception as e:
        print(f"--- ERROR CRÍTICO EN PUENTE --- {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendation/stimulus/{stimulus_id}")
def get_recommendations_by_stimulus_id(stimulus_id: int):
    """
    Este endpoint sigue igual para que el frontend pueda preguntar: ¿Ya terminó n8n?
    """
    try:
        recommendations_collection = pymongo_client.get_database("analyzer").get_collection("recommendations")
        result = recommendations_collection.find_one(
            {"stimulus_id": stimulus_id}, sort=[("_id", pymongo.DESCENDING)]
        )

        if result:
            result["_id"] = str(result["_id"]) # Convertir ObjectId a string para JSON
            return StimulusRecommendations(**result)
        else:
            return {
                "stimulus_id": stimulus_id,
                "folder_id": 0,
                "recommendations": [],
                "interpretations": {},
                "conclusion_en": "",
                "conclusion_es": "",
                "image_url": "",
                "benchmark": "",
                "status": 1,
            }
    except Exception as e:
        print(f"--- ERROR EN CONSULTA STIMULUS --- {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendation/folder/{folder_id}")
def get_recommendations_by_folder_id(folder_id: int):
    try:
        recommendations_collection = pymongo_client.get_database("analyzer").get_collection("recommendations")
        pipeline = [
            {"$match": {"folder_id": folder_id}},
            {"$sort": {"_id": pymongo.DESCENDING}},
            {"$group": {"_id": "$stimulus_id", "latest_doc": {"$first": "$$ROOT"}}},
        ]
        results = list(recommendations_collection.aggregate(pipeline))

        if results:
            for res in results:
                res["latest_doc"]["_id"] = str(res["latest_doc"]["_id"])
            return [StimulusRecommendations(**rec["latest_doc"]) for rec in results]
        else:
            raise HTTPException(status_code=404, detail="Carpeta no encontrada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
