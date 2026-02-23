import json
import os
import re
from typing import List

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
    # Eliminar ```json ... ``` o ``` ... ```
    text = re.sub(r'```json\s*|```\s*', '', text)
    return text.strip()

@router.post("/", response_model=RecommendationResponse)
async def generate_recommendations(stimulus: RecommendationRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR IA] OPENAI_API_KEY no encontrada en el entorno.")
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    client = OpenAI(api_key=api_key)
    
    error_recs = {
        "stimulus_id": stimulus.stimulus_id,
        "folder_id": stimulus.folder_id,
        "recommendations": [],
        "interpretations": {},
        "conclusion_en": "",
        "conclusion_es": "",
        "image_url": stimulus.image_url,
        "benchmark": stimulus.benchmark,
        "status": 5,
    }

    try:
        # 1. Crear el Thread
        thread = client.beta.threads.create()
        print(f"[DEBUG IA] Thread creado: {thread.id}")

        assistant_id = os.getenv("BABEL_ASSISTANT_ID")
        if not assistant_id:
            # Lógica para crear asistente si no existe...
            print("[DEBUG IA] Creando nuevo asistente...")
            assistant = client.beta.assistants.create(
                name="Babel Analyzer Assistant",
                instructions="You are a Neuromarketing expert...",
                model="gpt-4o",
            )
            assistant_id = assistant.id

        # 2. Construir contenido (Métricas y URLs)
        content_list = [
            {"type": "text", "text": f"Analyze this stimulus for the benchmark: {stimulus.benchmark}"},
            {"type": "text", "text": f"Metrics: {json.dumps(stimulus.metrics)}"},
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

        # 3. Ejecutar y esperar (Polling)
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, 
            assistant_id=assistant_id
        )

        if run.status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            message_content = messages.data[0].content[0].text.value
            
            print("[DEBUG IA] Respuesta cruda de OpenAI:", message_content)
            
            # LIMPIEZA DE JSON (Crucial para evitar errores)
            cleaned_content = clean_json_response(message_content)
            recommendations_data = json.loads(cleaned_content)

            recs = []
            for item in recommendations_data.get("recommendations", []):
                try:
                    recs.append(Recommendation(**item))
                except ValidationError as ve:
                    print(f"[WARN IA] Recomendación inválida omitida: {ve}")

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

            # Guardar en DB
            recommendations_collection.update_one(
                {"stimulus_id": stimulus.stimulus_id},
                {"$set": response_data},
                upsert=True
            )
            return response_data

        elif run.status == "failed":
            error_detail = run.last_error.message if run.last_error else "Unknown OpenAI error"
            print(f"[ERROR IA] Run falló: {error_detail}")
            error_recs["status"] = 5
            recommendations_collection.update_one(
                {"stimulus_id": stimulus.stimulus_id},
                {"$set": error_recs},
                upsert=True
            )
            return error_recs

    except OpenAIError as e:
        print(f"[ERROR IA] Error de API OpenAI: {str(e)}")
        return error_recs
    except Exception as e:
        print(f"[ERROR IA] Error inesperado en microservicio: {str(e)}")
        # Aquí verás el error de parsing si el JSON venía mal
        return error_recs

@router.get("/stimulus/{stimulus_id}", response_model=RecommendationResponse)
async def get_recommendation_by_stimulus(stimulus_id: int):
    result = recommendations_collection.find_one({"stimulus_id": stimulus_id})
    if result:
        result.pop("_id", None)
        return result
    raise HTTPException(status_code=404, detail="Recommendation not found")
