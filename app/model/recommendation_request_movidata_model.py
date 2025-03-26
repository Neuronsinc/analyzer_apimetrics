from app.model.metric_model import StimulusMetric
from pydantic import BaseModel
from typing import Dict, List


class RecommendationRequest(BaseModel):
    idUser: int
    layer_id: str
    project_id: int
    area: int
    pais: str
    fecha_inicial: str
    fecha_final: str
    dispositivos_unicos: float
    recurrencia_dispositivos: float
    recurrencia_dispositivos_hora: float
    dia_semana: Dict
    dia_mes: Dict
    hora_dia: Dict
    mov_departamento: List
    mov_municipio: List
    mov_zona: List
    dep_origen: List
    dep_origen_municipio: List
    dep_origen_zona: List
    dep_destino: List
    dep_destino_municipio: List
    dep_destino_zona: List