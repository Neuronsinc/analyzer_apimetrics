from app.model.metric_model import StimulusMetric
from pydantic import BaseModel
from typing import List


class RecommendationRequest(BaseModel):
    stimulus_id: int
    folder_id: int
    metrics: List[StimulusMetric]
    image_url: str
    benchmark: str