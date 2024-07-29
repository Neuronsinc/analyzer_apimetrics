from pydantic import BaseModel


class VRequest(BaseModel):
    id_stimulus: str
    analyzer_token: str
    idUser: str
    idCompany: str
    idLicense: str
    idFolder: str
    StimulusName: str
    FolderName: str
    Duration: str


class RedisReq(BaseModel):
    videoID: str 
    idUser:  str
    idCompany: str
    idLicense: str
    idStimulus: str
    token: str
    idFolder: str
    StimulusName: str
    FolderName: str
    UploadedAccount: str
    Duration: str
    idUserAnalyzer: str