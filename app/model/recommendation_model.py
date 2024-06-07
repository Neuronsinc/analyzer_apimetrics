from app.model.metric_model import StimulusMetric
from pydantic import BaseModel
from typing import List, Optional



class Recommendation(BaseModel):
    metrica: str
    recomendacion_en: Optional[str]
    recomendacion: str
    titulo: str
    titulo_en: Optional[str]
    fuente: str

class StimulusRecommendations(BaseModel):
    stimulus_id: int
    folder_id: int
    recommendations: List[Recommendation]
    image_url: str
    benchmark: str
    status: int