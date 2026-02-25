import re
from app.model.recommendation_model import Interpretations, Recommendation, StimulusRecommendations
from app.model.recommendation_request_model import RecommendationRequest
from fastapi import FastAPI, HTTPException, APIRouter
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv
import os
import json
from pydantic import BaseModel, ValidationError
from typing import List
import pymongo
from bson import ObjectId

# Cargar variables de entorno
load_dotenv("app/.env", override=False)

mongo_url = os.environ.get("MONGO_URL")
router = APIRouter()
pymongo_client = pymongo.MongoClient(mongo_url)

API_KEY = os.environ.get("OPENAI_KEY")
ASSISTANT_ID = os.environ.get("ASSISTANT_ID")

# Cliente OpenAI
client = OpenAI(api_key=API_KEY)

# Recuperar el asistente configurado
try:
    assistant = client.beta.assistants.retrieve(assistant_id=ASSISTANT_ID)
except Exception as e:
    print(f"--- ERROR AL RECUPERAR ASISTENTE --- ID: {ASSISTANT_ID} | Error: {str(e)}")

def clean_json_string(json_string):
    """
    Limpia la respuesta de OpenAI eliminando bloques de código markdown
    y caracteres extraños para asegurar un parseo JSON exitoso.
    """
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, json_string, flags=re.DOTALL)
    if match:
        cleaned = match.group(1).strip()
    else:
        cleaned = json_string.strip().replace("```json", "").replace("```", "")
    return cleaned

@router.post("/recommendation/")
def generate_recommendations(stimulus: RecommendationRequest):
    recommendations_collection = pymongo_client.get_database("analyzer").get_collection("recommendations")
    
    # Estructura base para respuesta de error/inicial
    error_recs_data = {
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
        "status": 5, 
    }

    try:
        # 1. Insertar registro inicial con status 3 (Procesando)
        initial_doc = error_recs_data.copy()
        initial_doc["status"] = 3
        inserted_recs = recommendations_collection.insert_one(initial_doc)
        inserted_id = inserted_recs.inserted_id

        # 2. Preparar métricas para el prompt
        metricas_str = ", ".join(f"{d.name}: {d.score}" for d in stimulus.metrics)

        # 3. Construir UN SOLO content_payload con texto e imágenes validadas
        content_payload = [
            {
                "type": "text", 
                "text": f"Imagen de {stimulus.benchmark} con métricas {metricas_str}. Analiza las imágenes visuales y genera el JSON con recomendaciones e interpretaciones."
            }
        ]

        # Lista de posibles imágenes a enviar
        images_to_validate = [
            stimulus.image_url,
            stimulus.heatmap_url,
            stimulus.gaze_plot_url,
            stimulus.focus_map_url,
            stimulus.aoi_url
        ]

        # Filtrar solo URLs válidas y agregarlas una sola vez
        for url in images_to_validate:
            if url and isinstance(url, str) and url.startswith("http"):
                content_payload.append({
                    "type": "image_url",
                    "image_url": {"url": url, "detail": "low"}
                })

        # 4. Crear hilo y enviar el mensaje consolidado
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=content_payload
        )

        # 5. Ejecutar y esperar respuesta
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, 
            assistant_id=assistant.id
        )

        # 6. Procesar resultado
        if run.status == "completed":
            messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
            raw_response = messages[0].content[0].text.value
            
            # Limpiar y cargar JSON
            json_data = json.loads(clean_json_string(raw_response))
            
            recommendations = [Recommendation(**item) for item in json_data.get("recomendaciones", [])]
            interpretations = Interpretations(**json_data.get("interpretaciones", {}))

            final_update = {
                "recommendations": [r.dict() for r in recommendations],
                "interpretations": interpretations.dict(),
                "conclusion_en": json_data.get("conclusion_en", ""),
                "conclusion_es": json_data.get("conclusion_es", ""),
                "status": 4 
            }

            recommendations_collection.update_one(
                {"_id": ObjectId(inserted_id)},
                {"$set": final_update}
            )

            return StimulusRecommendations(
                stimulus_id=stimulus.stimulus_id,
                folder_id=stimulus.folder_id,
                recommendations=recommendations,
                interpretations=interpretations,
                conclusion_en=final_update["conclusion_en"],
                conclusion_es=final_update["conclusion_es"],
                image_url=stimulus.image_url,
                benchmark=stimulus.benchmark,
                status=4
            )

        else:
            # LOG DETALLADO DE FALLO (Esto es lo que vimos en la terminal)
            error_detail = getattr(run, 'last_error', 'Sin detalle adicional')
            print(f"--- OPENAI RUN FAILED --- Status: {run.status} | Error: {error_detail}")
            
            recommendations_collection.update_one(
                {"_id": ObjectId(inserted_id)},
                {"$set": error_recs_data}
            )
            return error_recs_data

    except Exception as e:
        print(f"--- ERROR CRÍTICO EN RECOMMENDATION --- {str(e)}")
        if 'inserted_id' in locals():
            recommendations_collection.update_one(
                {"_id": ObjectId(inserted_id)},
                {"$set": error_recs_data}
            )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendation/stimulus/{stimulus_id}")
def get_recommendations_by_stimulus_id(stimulus_id: int):
    try:
        recommendations_collection = pymongo_client.get_database("analyzer").get_collection("recommendations")
        result = recommendations_collection.find_one(
            {"stimulus_id": stimulus_id}, sort=[("_id", pymongo.DESCENDING)]
        )

        if result:
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
        print(f"--- ERROR EN GET STIMULUS --- {str(e)}")
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
            return [StimulusRecommendations(**rec["latest_doc"]) for rec in results]
        else:
            raise HTTPException(status_code=404, detail="No se encontraron recomendaciones")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
