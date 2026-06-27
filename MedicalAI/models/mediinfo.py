from pydantic import BaseModel

class Mediinfo(BaseModel):
    id: int
    member_id:int
    modality: str
    file_name: str
    analyzed_text: str