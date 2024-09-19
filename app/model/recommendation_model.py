from app.model.metric_model import StimulusMetric
from pydantic import BaseModel
from typing import List, Optional

class Interpretations(BaseModel):
    heat_map_es: Optional[str]
    heat_map_en: Optional[str]
    gaze_plot_es: Optional[str]
    gaze_plot_en: Optional[str]
    focus_map_es: Optional[str]
    focus_map_en: Optional[str]
    aois_es: Optional[str]
    aois_en: Optional[str]

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
    interpretations: Optional[Interpretations ]
    conclusion_en: Optional[str]
    conclusion_es: Optional[str]
    image_url: str
    benchmark: str
    status: int