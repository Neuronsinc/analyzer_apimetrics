from app.model.metric_model import StimulusMetric
from pydantic import BaseModel
from typing import List, Optional

class Interpretations(BaseModel):
    heat_map_es: str
    heat_map_en: str
    gaze_plot_es: str
    gaze_plot_en: str
    focus_map_es: str
    focus_map_en: str
    aois_es: str
    aois_en: str

class Recommendation(BaseModel):
    metrica: str
    introduccion_es: Optional[str]
    introduccion_en: Optional[str]
    recomendacion_en: Optional[str]
    recomendacion: str
    titulo: str
    titulo_en: Optional[str]
    fuente: str

class StimulusRecommendations(BaseModel):
    stimulus_id: int
    folder_id: int
    recommendations: List[Recommendation]
    interpretations: Optional[Interpretations]
    image_url: str
    benchmark: str
    status: int
