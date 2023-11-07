from pydantic import BaseModel
from enum import Enum



class ARequest(BaseModel):
    id_stimulus: str
    analyzer_token: str
    clarity: str

class Apis(Enum):
    PREDICT = 1
    ATTENTION = 2
    FENGUI = 3