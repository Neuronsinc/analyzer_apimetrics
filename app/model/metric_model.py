from pydantic import BaseModel

class StimulusMetric(BaseModel):
    name: str
    score: float