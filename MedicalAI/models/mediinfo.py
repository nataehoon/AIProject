from pydantic import BaseModel
from typing import Optional

class Mediinfo(BaseModel):
    id: int = 0
    member_id:int = 0
    modality: str = ""
    file_name: str = ""
    analyzed_text: str = ""