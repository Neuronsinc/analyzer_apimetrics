from pydantic import BaseModel
from enum import Enum

class Stimulus(BaseModel):
    image_url: str
    title: str
    id_folder: int
    filename: str
    id_stimulus: str

class ApiCredential(BaseModel):
    clave: str
    url: str


