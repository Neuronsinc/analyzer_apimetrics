import re
from app.model.recommendation_model import Interpretations, Recommendation, StimulusRecommendations
from app.model.recommendation_movidata_model import LayerRecommendations, Recommendations
from app.model.recommendation_request_movidata_model import RecommendationRequest
from fastapi import FastAPI, HTTPException, APIRouter
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv
import os
import json
from pydantic import BaseModel, ValidationError
from typing import List
import pymongo
from bson import ObjectId
import redis

load_dotenv("app\.env", override=False)

mongo_url = os.environ.get("MONGO_URL")

router = APIRouter()
pymongo_client = pymongo.MongoClient(mongo_url)

API_KEY = os.environ.get("OPENAI_KEY")
ASSISTANT_ID = os.environ.get("ASSISTANT_MOVIDATA_ID")

client = OpenAI(api_key=API_KEY)

assistant = client.beta.assistants.retrieve(assistant_id=ASSISTANT_ID)


def clean_json_string(json_string):
    pattern = r"^```json\s*(.*?)\s*```$"
    cleaned_string = re.sub(pattern, r"\1", json_string, flags=re.DOTALL)
    return cleaned_string.strip()


def send_to_redis(obj, canal):
    connection = redis.Redis.from_url(os.getenv('REDIS_URL'))

    cadena_json = json.dumps(obj)

    connection.rpush(canal, cadena_json)
    connection.publish(canal, cadena_json)
    


@router.post("/recommendation/movidata/")
def generate_recommendations(layer: RecommendationRequest):
    recommendations_collection = pymongo_client.get_database("analyzer").get_collection("recommendations_movidata")
    try:

        error_recs = {
            "idUser": layer.idUser,
            "layer_id": layer.layer_id,
            "project_id": layer.project_id,
            "recommendations": [],
            "interpretacion": "",
            "pais": layer.pais,
            "fecha_inicial": layer.fecha_inicial,
            "fecha_final": layer.fecha_final,
            "area": layer.area,
            "dispositivos_unicos": layer.dispositivos_unicos,
            "recurrencia_dispositivos": layer.recurrencia_dispositivos,
            "recurrencia_dispositivos_hora": layer.recurrencia_dispositivos_hora,
            "dia_semana": layer.dia_semana,
            "dia_mes": layer.dia_mes,
            "hora_dia": layer.hora_dia,
            "mov_departamento": layer.mov_departamento,
            "mov_municipio": layer.mov_municipio,
            "mov_zona": layer.mov_zona,
            "dep_origen": layer.dep_origen,
            "dep_origen_municipio": layer.dep_origen_municipio,
            "dep_origen_zona": layer.dep_origen_zona,
            "dep_destino": layer.dep_destino,
            "dep_destino_municipio": layer.dep_destino_municipio,
            "dep_destino_zona": layer.dep_destino_zona,
            "status": 5
        }

        inserted_recs = recommendations_collection.insert_one(
            {
                "layer_id": layer.layer_id,
                "project_id": layer.project_id,
                "recommendations": [],
                "interpretacion": "",
                "pais": layer.pais,
                "fecha_inicial": layer.fecha_inicial,
                "fecha_final": layer.fecha_final,
                "area": layer.area,
                "dispositivos_unicos": layer.dispositivos_unicos,
                "recurrencia_dispositivos": layer.recurrencia_dispositivos,
                "recurrencia_dispositivos_hora": layer.recurrencia_dispositivos_hora,
                "dia_semana": layer.dia_semana,
                "dia_mes": layer.dia_mes,
                "hora_dia": layer.hora_dia,
                "mov_departamento": layer.mov_departamento,
                "mov_municipio": layer.mov_municipio,
                "mov_zona": layer.mov_zona,
                "dep_origen": layer.dep_origen,
                "dep_origen_municipio": layer.dep_origen_municipio,
                "dep_origen_zona": layer.dep_origen_zona,
                "dep_destino": layer.dep_destino,
                "dep_destino_municipio": layer.dep_destino_municipio,
                "dep_destino_zona": layer.dep_destino_zona,
                "status": 3
            }
        )

        thread = client.beta.threads.create()

        json_data = json.dumps(layer, default=str)

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=json_data
        )

        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistant.id
        )

        if run.status == "completed":
            messages = list(
                client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id)
            )

            message_content = messages[0].content[0].text
            message_value = clean_json_string(message_content.value) # Eliminar "```" y "```json" si OpenAI responde en markdown
            response = json.loads(message_value)
            recommendations = [Recommendations(**item) for item in response["recomendaciones"]]
            recs = LayerRecommendations(
                layer_id=layer.layer_id,
                project_id=layer.project_id,
                recommendations=recommendations,
                interpretacion= response["interpretacion_general"],
                pais=layer.pais,
                fecha_inicial=layer.fecha_inicial,
                fecha_final=layer.fecha_final,
                area=layer.area,
                dispositivos_unicos=layer.dispositivos_unicos,
                recurrencia_dispositivos=layer.recurrencia_dispositivos,
                recurrencia_dispositivos_hora=layer.recurrencia_dispositivos_hora,
                dia_semana=layer.dia_semana,
                dia_mes=layer.dia_mes,
                hora_dia=layer.hora_dia,
                mov_departamento=layer.mov_departamento,
                mov_municipio=layer.mov_municipio,
                mov_zona=layer.mov_zona,
                dep_origen=layer.dep_origen,
                dep_origen_municipio=layer.dep_origen_municipio,
                dep_origen_zona=layer.dep_origen_zona,
                dep_destino=layer.dep_destino,
                dep_destino_municipio=layer.dep_destino_municipio,
                dep_destino_zona=layer.dep_destino_zona,
                status=4
            )

            recommendations_collection.update_one(
                {"_id": ObjectId(inserted_recs.inserted_id)},
                {
                    "$set": {
                        "layer_id": layer.layer_id,
                        "project_id": layer.project_id,
                        "recommendations": [r.dict() for r in recommendations],
                        "interpretacion": response["interpretacion_general"],
                        "pais": layer.pais,
                        "fecha_inicial": layer.fecha_inicial,
                        "fecha_final": layer.fecha_final,
                        "area": layer.area,
                        "dispositivos_unicos": layer.dispositivos_unicos,
                        "recurrencia_dispositivos": layer.recurrencia_dispositivos,
                        "recurrencia_dispositivos_hora": layer.recurrencia_dispositivos_hora,
                        "dia_semana": layer.dia_semana,
                        "dia_mes": layer.dia_mes,
                        "hora_dia": layer.hora_dia,
                        "mov_departamento": layer.mov_departamento,
                        "mov_municipio": layer.mov_municipio,
                        "mov_zona": layer.mov_zona,
                        "dep_origen": layer.dep_origen,
                        "dep_origen_municipio": layer.dep_origen_municipio,
                        "dep_origen_zona": layer.dep_origen_zona,
                        "dep_destino": layer.dep_destino,
                        "dep_destino_municipio": layer.dep_destino_municipio,
                        "dep_destino_zona": layer.dep_destino_zona,
                        "status": 4,
                    }
                },
            )

            # aviso a redis
            mi_objeto = {
                'idUser': layer.idUser,
                'layer_id': layer.layer_id,
                'project_id':layer.project_id,
                'recommendations': [rec.dict() for rec in recommendations],
                'interpretacion': response["interpretacion_general"],
                'pais':layer.pais,
                'fecha_inicial':layer.fecha_inicial,
                'fecha_final':layer.fecha_final,
                'area':layer.area,
                'dispositivos_unicos':layer.dispositivos_unicos,
                'recurrencia_dispositivos':layer.recurrencia_dispositivos,
                'recurrencia_dispositivos_hora':layer.recurrencia_dispositivos_hora,
                'dia_semana':layer.dia_semana,
                'dia_mes':layer.dia_mes,
                'hora_dia':layer.hora_dia,
                'mov_departamento':layer.mov_departamento,
                'mov_municipio':layer.mov_municipio,
                'mov_zona':layer.mov_zona,
                'dep_origen':layer.dep_origen,
                'dep_origen_municipio':layer.dep_origen_municipio,
                'dep_origen_zona':layer.dep_origen_zona,
                'dep_destino':layer.dep_destino,
                'dep_destino_municipio':layer.dep_destino_municipio,
                'dep_destino_zona':layer.dep_destino_zona,
                'status':4
            }

            send_to_redis(mi_objeto, 'Progreso_movidata_ia')

            return recs
        elif run.status == "failed":
            print(run.last_error.code)
            recommendations_collection.update_one(
                {"_id": ObjectId(inserted_recs.inserted_id)},
                {"$set": error_recs},
            )
            send_to_redis(error_recs, 'Fallo_movidata_ia')
            return error_recs
    except OpenAIError as e:
        recommendations_collection.update_one(
            {"_id": ObjectId(inserted_recs.inserted_id)},
            {"$set": error_recs},
        )
        send_to_redis(error_recs, 'Fallo_movidata_ia')
        raise HTTPException(status_code=500, detail=f"OpenAI Error: {e}")
    except ValidationError as e:
        recommendations_collection.update_one(
            {"_id": ObjectId(inserted_recs.inserted_id)},
            {"$set": error_recs},
        )
        send_to_redis(error_recs, 'Fallo_movidata_ia')
        raise HTTPException(status_code=400, detail=f"Validation Error: {e.json()}")
    except ValueError as e:
        recommendations_collection.update_one(
            {"_id": ObjectId(inserted_recs.inserted_id)},
            {"$set": error_recs},
        )
        send_to_redis(error_recs, 'Fallo_movidata_ia')
        raise HTTPException(status_code=500, detail=f"ValueError: {e}")


@router.get("/recommendation/movidata/layer/{layer_id}")
def get_recommendations_by_stimulus_id(layer_id: str):
    try:
        recommendations_collection = pymongo_client.get_database("analyzer").get_collection("recommendations_movidata")
        result = recommendations_collection.find_one(
            {"layer_id": layer_id}, sort=[("_id", pymongo.DESCENDING)]
        )

        if result:
            recommendations = LayerRecommendations(**result)
            return recommendations
        else:
            return {
            "layer_id": layer_id,
            "project_id": "",
            "recommendations": [],
            "interpretacion": "",
            "pais": "",
            "fecha_inicial": "",
            "fecha_final": "",
            "area": 0,
            "dispositivos_unicos": 0,
            "recurrencia_dispositivos": {},
            "recurrencia_dispositivos_hora": {},
            "dia_semana": {},
            "dia_mes": {},
            "hora_dia": {},
            "mov_departamento": [],
            "mov_municipio": [],
            "mov_zona": [],
            "dep_origen": [],
            "dep_origen_municipio": [],
            "dep_origen_zona": [],
            "dep_destino": [],
            "dep_destino_municipio": [],
            "dep_destino_zona": [],
            "status": 1
            }

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Validation Error: {e.json()}")
