from app.model.metric_model import StimulusMetric
from pydantic import BaseModel
from typing import List


class RecommendationRequest(BaseModel):
    stimulus_id: int
    folder_id: int
    metrics: List[StimulusMetric]
    image_url: str
    gaze_plot_url: str
    heatmap_url: str
    focus_map_url: str
    aoi_url: str
    benchmark: str