from app.model.metric_model import StimulusMetric
from pydantic import BaseModel
from typing import List



class Recommendation(BaseModel):
    metrica: str
    recomendacion: str
    titulo: str
    fuente: str

class StimulusRecommendations(BaseModel):
    stimulus_id: int
    folder_id: int
    recommendations: List[Recommendation]
    image_url: str
    benchmark: str