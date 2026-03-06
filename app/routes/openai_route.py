import os
import json
from typing import List, Literal, Optional

import pymongo
from bson import ObjectId
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from openai import OpenAI, OpenAIError
from pydantic import BaseModel, ValidationError

from app.model.recommendation_model import (
    Interpretations,
    Recommendation,
    StimulusRecommendations,
)
from app.model.recommendation_request_model import RecommendationRequest

load_dotenv("app\\.env", override=False)

mongo_url = os.environ.get("MONGO_URL")
api_key = os.environ.get("OPENAI_KEY")

# Nuevo: ya no dependes de ASSISTANT_ID
# Reutiliza tu vector store actual
VECTOR_STORE_ID = os.environ.get("OPENAI_VECTOR_STORE_ID", "vs_MUuUwETHHjWg010XP8zuF5Pu")

# Modelo recomendado para un flujo multimodal + JSON estructurado
MODEL_NAME = os.environ.get("OPENAI_MODEL", "gpt-5")

router = APIRouter()
pymongo_client = pymongo.MongoClient(mongo_url)
client = OpenAI(api_key=api_key)

SYSTEM_PROMPT = """
Tienes dos tareas. La primera es recomendar cambios en una imagen dada para "aumentar o disminuir la puntuación en cada métrica, de modo que esté dentro del benchmark para ese tipo de imagen", basándote en la imagen recibida, las métricas y la diferencia entre estas y los benchmarks. Tu segunda tarea es interpretar diferentes gráficos de la imagen, incluyendo mapa de calor, mapa de secuencia visual, mapa de opacidad y el mapa de areas de interés. Para esto recibirás 4 imágenes adicionales, una por cada grafico.

***Tarea 1: Recomendaciones***
El archivo `benchmarks.txt` contiene los benchmarks para diferentes tipos de imágenes.
El archivo `DescriptorDeNeurometricas.pdf` contiene las descripciones de las métricas existentes y sus puntajes.

Accede al resto de archivos disponibles para obtener información sobre métricas y posibles recomendaciones. Utiliza los archivos que tengas disponibles para generar recomendaciones e interpretaciones mas detalladas.

Las métricas pueden tener valores demasiado altos; los valores de las métricas no deben superar los valores del benchmark.

La severidad de las recomendaciones dependerá de qué tan alejado esté el valor de la métrica del benchmark actual.

Las recomendaciones deben ser coherentes con el contenido de la imagen.
Debes generar una recomendación por métrica.
Las recomendaciones deben mencionar elementos de la imagen proporcionada y deben ser concisas.

Deberas generar tambien una introduccion en la que se indique porque la imagen obtuvo esta puntuacion (que elementos de la imagen contribuyen a la puntuacion obtenida) y si esta dentro del benchmark.

Agrega un campo 'fuente' por cada recomendación cuyo valor sea estrictamente uno de los siguientes:
- Ariely, D. (2012). Predictably irrational.
- Barden, P. (2023). Decoded The science behind why we buy. John Wiley & Sons, Inc.
- Heath, R. (2012). Seducing the Subconscious.
- Leach, W. (2018). Marketing to mindstates The practical guide to applying behaviour design to research and marketing.
- Ramsøy, T. Z. (2015). Introduction to Neuromarketing & Consumer Neuroscience
- Genco, S. J., Pohlmann, A. P., & Steidl, P. (2013). Neuromarketing for dummies. John Wiley & Sons Canada Ltd.

Incluye un titulo por cada recomendación que resuma el contenido de la misma.
Resalta con negrita la parte mas importante del texto de la recomendacion.

***Tarea 2: Interpretaciones***
Deberas retornar una interpretacion por cada grafico. En total son 4. Debes utilizar la informacion del archivo "MapReports.md" para generar interpretaciones de los resultados de cada uno.

Utiliza las puntuaciones de las metricas dadas para mejorar el contenido de las interpretaciones.
Deberas generar interpretaciones detalladas las cuales deben incluir la razon por la cual se obtienen estos resultados.

Para el gaze plot deberas indicar cuales son los puntos de atencion principales (rojos), secundarios (amarillo) y terciarios (verdes).

No confundas el gaze plot con el heat map. Ambos usan los mismos colores pero el gaze plot incluye circulos con numeros unidos por lineas, mientras que el heatmap incluye manchas que indican la intensidad de atencion.

Resalta con negrita la parte mas importante del texto de la interpretacion.

Deberas generar tambien una conclusion general que incluya elementos de la imagen y el texto generado anteriormente.

Debes responder solamente con el objeto JSON requerido por el schema.
""".strip()


RESPONSE_SCHEMA = {
    "name": "analyzer_recommendations",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "recomendaciones": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "metrica": {"type": "string"},
                        "introduccion_es": {"type": "string"},
                        "introduccion_en": {"type": "string"},
                        "recomendacion": {"type": "string"},
                        "recomendacion_en": {"type": "string"},
                        "titulo": {"type": "string"},
                        "titulo_en": {"type": "string"},
                        "fuente": {
                            "type": "string",
                            "enum": [
                                "Ariely, D. (2012). Predictably irrational.",
                                "Barden, P. (2023). Decoded The science behind why we buy. John Wiley & Sons, Inc.",
                                "Heath, R. (2012). Seducing the Subconscious.",
                                "Leach, W. (2018). Marketing to mindstates The practical guide to applying behaviour design to research and marketing.",
                                "Ramsøy, T. Z. (2015). Introduction to Neuromarketing & Consumer Neuroscience",
                                "Genco, S. J., Pohlmann, A. P., & Steidl, P. (2013). Neuromarketing for dummies. John Wiley & Sons Canada Ltd."
                            ]
                        }
                    },
                    "required": [
                        "metrica",
                        "introduccion_es",
                        "introduccion_en",
                        "recomendacion",
                        "recomendacion_en",
                        "titulo",
                        "titulo_en",
                        "fuente"
                    ]
                }
            },
            "interpretaciones": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "heat_map_es": {"type": "string"},
                    "heat_map_en": {"type": "string"},
                    "gaze_plot_es": {"type": "string"},
                    "gaze_plot_en": {"type": "string"},
                    "focus_map_es": {"type": "string"},
                    "focus_map_en": {"type": "string"},
                    "aois_es": {"type": "string"},
                    "aois_en": {"type": "string"}
                },
                "required": [
                    "heat_map_es",
                    "heat_map_en",
                    "gaze_plot_es",
                    "gaze_plot_en",
                    "focus_map_es",
                    "focus_map_en",
                    "aois_es",
                    "aois_en"
                ]
            },
            "conclusion_en": {"type": "string"},
            "conclusion_es": {"type": "string"}
        },
        "required": [
            "recomendaciones",
            "interpretaciones",
            "conclusion_en",
            "conclusion_es"
        ]
    }
}


def build_metrics_text(metrics) -> str:
    return ", ".join(f"{m.name}: {m.score}" for m in metrics)


def build_user_input(stimulus: RecommendationRequest):
    metricas = build_metrics_text(stimulus.metrics)

    return [
        {
            "role": "system",
            "content": [
                {
                    "type": "input_text",
                    "text": SYSTEM_PROMPT
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        f"Tipo de benchmark: {stimulus.benchmark}. "
                        f"Analiza el estímulo y sus mapas asociados. "
                        f"Estas son las métricas del estímulo: {metricas}. "
                        f"Debes consultar el conocimiento del vector store para benchmarks, "
                        f"descriptores de neurométricas y guías de interpretación de mapas. "
                        f"Devuelve únicamente el JSON estructurado solicitado."
                    )
                },
                {
                    "type": "input_image",
                    "image_url": stimulus.image_url,
                    "detail": "low"
                },
                {
                    "type": "input_image",
                    "image_url": stimulus.heatmap_url,
                    "detail": "low"
                },
                {
                    "type": "input_image",
                    "image_url": stimulus.gaze_plot_url,
                    "detail": "low"
                },
                {
                    "type": "input_image",
                    "image_url": stimulus.focus_map_url,
                    "detail": "low"
                },
                {
                    "type": "input_image",
                    "image_url": stimulus.aoi_url,
                    "detail": "low"
                }
            ]
        }
    ]


@router.post("/recommendation/")
def generate_recommendations(stimulus: RecommendationRequest):
    recommendations_collection = (
        pymongo_client.get_database("analyzer").get_collection("recommendations")
    )

    inserted_recs = None

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
        inserted_recs = recommendations_collection.insert_one(
            {
                "stimulus_id": stimulus.stimulus_id,
                "folder_id": stimulus.folder_id,
                "recommendations": [],
                "interpretations": {},
                "conclusion_en": "",
                "conclusion_es": "",
                "image_url": stimulus.image_url,
                "benchmark": stimulus.benchmark,
                "status": 3,
            }
        )

        response = client.responses.create(
            model=MODEL_NAME,
            input=build_user_input(stimulus),
            tools=[
                {
                    "type": "file_search",
                    "vector_store_ids": [VECTOR_STORE_ID]
                }
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": RESPONSE_SCHEMA["name"],
                    "strict": RESPONSE_SCHEMA["strict"],
                    "schema": RESPONSE_SCHEMA["schema"]
                }
            }
        )

        # Con Structured Outputs esto debería ser JSON válido siempre
        raw_json = response.output_text
        parsed = json.loads(raw_json)

        recommendations = [
            Recommendation(**item) for item in parsed["recomendaciones"]
        ]

        interpretations = Interpretations(**parsed["interpretaciones"])

        stimulus_recs = StimulusRecommendations(
            stimulus_id=stimulus.stimulus_id,
            folder_id=stimulus.folder_id,
            recommendations=recommendations,
            interpretations=interpretations,
            conclusion_en=parsed["conclusion_en"],
            conclusion_es=parsed["conclusion_es"],
            image_url=stimulus.image_url,
            benchmark=stimulus.benchmark,
            status=4,
        )

        recommendations_collection.update_one(
            {"_id": ObjectId(inserted_recs.inserted_id)},
            {
                "$set": {
                    "stimulus_id": stimulus.stimulus_id,
                    "folder_id": stimulus.folder_id,
                    "recommendations": [r.dict() for r in recommendations],
                    "interpretations": interpretations.dict(),
                    "conclusion_en": parsed["conclusion_en"],
                    "conclusion_es": parsed["conclusion_es"],
                    "image_url": stimulus.image_url,
                    "benchmark": stimulus.benchmark,
                    "status": 4,
                }
            },
        )

        return stimulus_recs

    except OpenAIError as e:
        if inserted_recs:
            recommendations_collection.update_one(
                {"_id": ObjectId(inserted_recs.inserted_id)},
                {"$set": error_recs},
            )
        raise HTTPException(status_code=500, detail=f"OpenAI Error: {str(e)}")

    except ValidationError as e:
        if inserted_recs:
            recommendations_collection.update_one(
                {"_id": ObjectId(inserted_recs.inserted_id)},
                {"$set": error_recs},
            )
        raise HTTPException(status_code=400, detail=f"Validation Error: {e.json()}")

    except json.JSONDecodeError as e:
        if inserted_recs:
            recommendations_collection.update_one(
                {"_id": ObjectId(inserted_recs.inserted_id)},
                {"$set": error_recs},
            )
        raise HTTPException(status_code=500, detail=f"Invalid JSON returned by model: {str(e)}")

    except Exception as e:
        if inserted_recs:
            recommendations_collection.update_one(
                {"_id": ObjectId(inserted_recs.inserted_id)},
                {"$set": error_recs},
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendation/stimulus/{stimulus_id}")
def get_recommendations_by_stimulus_id(stimulus_id: int):
    try:
        recommendations_collection = (
            pymongo_client.get_database("analyzer").get_collection("recommendations")
        )
        result = recommendations_collection.find_one(
            {"stimulus_id": stimulus_id}, sort=[("_id", pymongo.DESCENDING)]
        )

        if result:
            return StimulusRecommendations(**result)

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

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Validation Error: {e.json()}")


@router.get("/recommendation/folder/{folder_id}")
def get_recommendations_by_folder_id(folder_id: int):
    try:
        recommendations_collection = (
            pymongo_client.get_database("analyzer").get_collection("recommendations")
        )

        pipeline = [
            {"$match": {"folder_id": folder_id}},
            {"$sort": {"_id": pymongo.DESCENDING}},
            {"$group": {"_id": "$stimulus_id", "latest_doc": {"$first": "$$ROOT"}}},
        ]

        results = list(recommendations_collection.aggregate(pipeline))

        if results:
            return [StimulusRecommendations(**rec["latest_doc"]) for rec in results]

        raise HTTPException(
            status_code=404,
            detail="No se encontraron recomendaciones para esta carpeta",
        )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Validation Error: {e.json()}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
