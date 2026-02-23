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

load_dotenv("app\.env", override=False)

mongo_url = os.environ.get("MONGO_URL")

router = APIRouter()
pymongo_client = pymongo.MongoClient(mongo_url)

API_KEY = os.environ.get("OPENAI_KEY")
ASSISTANT_ID = os.environ.get("ASSISTANT_ID")

client = OpenAI(api_key=API_KEY)

assistant = client.beta.assistants.retrieve(assistant_id=ASSISTANT_ID)


def clean_json_string(json_string):
    pattern = r"^```json\s*(.*?)\s*```$"
    cleaned_string = re.sub(pattern, r"\1", json_string, flags=re.DOTALL)
    return cleaned_string.strip()


@router.post("/recommendation/")
def generate_recommendations(stimulus: RecommendationRequest):
    recommendations_collection = pymongo_client.get_database("analyzer").get_collection("recommendations")
    try:

        error_recs = {
            "stimulus_id": stimulus.stimulus_id,
            "folder_id": stimulus.folder_id,
            "recommendations": [],
            "interpretations": [],
            "conclusion_en": "",
            "conclusion_es": "",
            "image_url": stimulus.image_url,
            "benchmark": stimulus.benchmark,
            "status": 5,
        }

        inserted_recs = recommendations_collection.insert_one(
            {
                "stimulus_id": stimulus.stimulus_id,
                "folder_id": stimulus.folder_id,
                "recommendations": [],
                "interpretations": [],
                "conclusion_en": "",
                "conclusion_es": "",
                "image_url": stimulus.image_url,
                "benchmark": stimulus.benchmark,
                "status": 3,
            }
        )

        metricas = ", ".join(f"{d.name}: {d.score}" for d in stimulus.metrics)

        thread = client.beta.threads.create()

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=[
                {
                    "type": "text",
                    "text": f"imagen de {stimulus.benchmark} con metricas {metricas}",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": stimulus.image_url, "detail": "low"},
                },
                {
                    "type": "image_url",
                    "image_url": {"url": stimulus.heatmap_url, "detail": "low"},
                },
                {
                    "type": "image_url",
                    "image_url": {"url": stimulus.gaze_plot_url, "detail": "low"},
                },
                {
                    "type": "image_url",
                    "image_url": {"url": stimulus.focus_map_url, "detail": "low"},
                },
                {
                    "type": "image_url",
                    "image_url": {"url": stimulus.aoi_url, "detail": "low"},
                }

            ],
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
            recommendations = [Recommendation(**item) for item in response["recomendaciones"]]
            stimulus_recs = StimulusRecommendations(
                stimulus_id=stimulus.stimulus_id,
                folder_id=stimulus.folder_id,
                recommendations=recommendations,
                conclusion_en=response["conclusion_en"],
                conclusion_es=response["conclusion_es"],
                interpretations=Interpretations(**response["interpretaciones"]),
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
                        "interpretations": Interpretations(**response["interpretaciones"]).dict(),
                        "conclusion_en": response["conclusion_en"],
                        "conclusion_es": response["conclusion_es"],
                        "image_url": stimulus.image_url,
                        "benchmark": stimulus.benchmark,
                        "status": 4,
                    }
                },
            )

            return stimulus_recs
        elif run.status == "failed":
            print(run.last_error.code)
            recommendations_collection.update_one(
                {"_id": ObjectId(inserted_recs.inserted_id)},
                {"$set": error_recs},
            )
            return error_recs
    except OpenAIError as e:
        recommendations_collection.update_one(
            {"_id": ObjectId(inserted_recs.inserted_id)},
            {"$set": error_recs},
        )
        raise HTTPException(status_code=500, detail=f"OpenAI Error: {e}")
    except ValidationError as e:
        recommendations_collection.update_one(
            {"_id": ObjectId(inserted_recs.inserted_id)},
            {"$set": error_recs},
        )
        raise HTTPException(status_code=400, detail=f"Validation Error: {e.json()}")
    except ValueError as e:
        recommendations_collection.update_one(
            {"_id": ObjectId(inserted_recs.inserted_id)},
            {"$set": error_recs},
        )
        raise HTTPException(status_code=500, detail=f"ValueError: {e}")


@router.get("/recommendation/stimulus/{stimulus_id}")
def get_recommendations_by_stimulus_id(stimulus_id: int):
    try:
        recommendations_collection = pymongo_client.get_database("analyzer").get_collection("recommendations")
        result = recommendations_collection.find_one(
            {"stimulus_id": stimulus_id}, sort=[("_id", pymongo.DESCENDING)]
        )

        if result:
            recommendations = StimulusRecommendations(**result)
            return recommendations
        else:
            return {
                "stimulus_id": stimulus_id,
                "folder_id": 0,
                "recommendations": [],
                "interpretations":[],
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
        recommendations_collection = pymongo_client.get_database("analyzer").get_collection("recommendations")

        pipeline = [
            {"$match": {"folder_id": folder_id}},
            {"$sort": {"_id": pymongo.DESCENDING}},
            {"$group": {"_id": "$stimulus_id", "latest_doc": {"$first": "$$ROOT"}}},
        ]

        results = list(recommendations_collection.aggregate(pipeline))

        if results:
            recommendations = [
                StimulusRecommendations(**rec["latest_doc"]) for rec in results
            ]
            return recommendations
        else:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron recomendaciones para esta carpeta",
            )

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Validation Error: {e.json()}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
