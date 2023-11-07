from pydantic import BaseModel


# data = {'study_name': studySettings["study_name"]
#         , 'study_type': studySettings["study_type"]
#         , 'content_type': studySettings["content_type"]
#         , 'tasks[0]': 'focus'
#         , 'tasks[1]': 'clarity_score'}

class StudySettings(BaseModel):
    study_name: str
    study_type: str
    content_type: str