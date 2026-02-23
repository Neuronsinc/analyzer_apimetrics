import json
import os
import re
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from openai import OpenAI, OpenAIError
from pydantic import ValidationError

from app.apis.s3.s3manager import S3Manager
from app.model.api_model import ApiModel
from app.model.recommendation_model import Recommendation, RecommendationResponse
from app.model.recommendation_request_model import RecommendationRequest

router = APIRouter()

# Configuración de MongoDB (asumiendo que viene de un modelo de base de datos)
from Api import db
recommendations_collection = db["recommendations"]

def clean_json_response(text: str) -> str:
    """Elimina bloques de código markdown y espacios en blanco innecesarios."""
    text = re.sub(r'```json\s*|```\s*', '', text)
    return text.strip()

@router.post("/", response_model=RecommendationResponse)
async def generate_recommendations(stimulus: RecommendationRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR IA] OPENAI_API_KEY no configurada.")
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    client = OpenAI(api_key=api_key)
    
    # Objeto base para reportar errores
    error_recs = {
        "stimulus_id": stimulus.stimulus_id,
        "folder_id": stimulus.folder_id,
        "recommendations": [],
        "interpretations": {
            "heat_map_es": None, "heat_map_en": None, 
            "gaze_plot_es": None, "gaze_plot_en": None, 
            "focus_map_es": None, "focus_map_en": None,
            "aois_es": None, "aois_en": None
        },
        "conclusion_en": "Error técnico detectado.",
        "conclusion_es": "Error técnico detectado.",
        "image_url": stimulus.image_url,
        "benchmark": stimulus.benchmark,
        "status": 5,
    }

    try:
        # 1. Verificar Asistente
        assistant_id = os.getenv("BABEL_ASSISTANT_ID")
        if not assistant_id:
            print("[WARN IA] BABEL_ASSISTANT_ID no definido, usando fallback...")
            # Aquí podrías poner un ID de respaldo o crear uno dinámicamente

        # 2. Crear Thread y Mensaje
        thread = client.beta.threads.create()
        print(f"[DEBUG IA] Thread: {thread.id} | Procesando estimulo: {stimulus.stimulus_id}")

        content_list = [
            {"type": "text", "text": f"Analyze for benchmark: {stimulus.benchmark}. Return JSON with 'recommendations' and 'interpretations' keys."},
            {"type": "text", "text": f"Scores: {json.dumps(stimulus.metrics)}"},
            {"type": "image_url", "image_url": {"url": stimulus.image_url}},
            {"type": "image_url", "image_url": {"url": stimulus.heatmap_url}},
            {"type": "image_url", "image_url": {"url": stimulus.focus_map_url}},
            {"type": "image_url", "image_url": {"url": stimulus.gaze_plot_url}},
            {"type": "image_url", "image_url": {"url": stimulus.aoi_url}}
        ]

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=content_list
        )

        # 3. Ejecutar Run
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, 
            assistant_id=assistant_id
        )

        print(f"[DEBUG IA] Run ID: {run.id} | Status: {run.status}")

        if run.status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            message_content = messages.data[0].content[0].text.value
            
            # Limpiar y parsear JSON
            cleaned_content = clean_json_response(message_content)
            try:
                recommendations_data = json.loads(cleaned_content)
            except json.JSONDecodeError as je:
                print(f"[ERROR IA] JSON inválido de OpenAI: {cleaned_content}")
                error_recs["conclusion_es"] = f"Error de formato IA: {str(je)}"
                return error_recs

            recs = []
            for item in recommendations_data.get("recommendations", []):
                try:
                    recs.append(Recommendation(**item))
                except ValidationError:
                    continue

            response_data = {
                "stimulus_id": stimulus.stimulus_id,
                "folder_id": stimulus.folder_id,
                "recommendations": recs,
                "interpretations": recommendations_data.get("interpretations", {}),
                "conclusion_en": recommendations_data.get("conclusion_en", ""),
                "conclusion_es": recommendations_data.get("conclusion_es", ""),
                "image_url": stimulus.image_url,
                "benchmark": stimulus.benchmark,
                "status": 1,
            }

            recommendations_collection.update_one(
                {"stimulus_id": stimulus.stimulus_id},
                {"$set": response_data},
                upsert=True
            )
            return response_data

        elif run.status == "failed":
            error_msg = run.last_error.message if run.last_error else "Fallo desconocido en OpenAI"
            print(f"[ERROR IA] El Run de OpenAI falló: {error_msg}")
            error_recs["conclusion_es"] = f"OpenAI Falló: {error_msg}"
            recommendations_collection.update_one(
                {"stimulus_id": stimulus.stimulus_id},
                {"$set": error_recs},
                upsert=True
            )
            return error_recs

        else:
            print(f"[WARN IA] Run terminó con estado inesperado: {run.status}")
            error_recs["conclusion_es"] = f"Estado inesperado: {run.status}"
            return error_recs

    except OpenAIError as oe:
        print(f"[ERROR IA] Excepción de OpenAI: {str(oe)}")
        error_recs["conclusion_es"] = f"Error de API: {str(oe)}"
        return error_recs
    except Exception as e:
        print(f"[ERROR IA] Error general: {str(e)}")
        error_recs["conclusion_es"] = f"Error interno: {str(e)}"
        return error_recs

@router.get("/stimulus/{stimulus_id}", response_model=RecommendationResponse)
async def get_recommendation_by_stimulus(stimulus_id: int):
    result = recommendations_collection.find_one({"stimulus_id": stimulus_id})
    if result:
        result.pop("_id", None)
        return result
    raise HTTPException(status_code=404, detail="Recommendation not found")
