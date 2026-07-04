from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Mediinfo(BaseModel):
    id: int = 0
    member_id:int = 0
    modality: str = ""
    file_name: str = ""
    analyzed_text: str = ""

class VersionInfo(BaseModel):
    id: int = 0
    version: str = ""
    active: bool = False

class QA_RawData(BaseModel):
    id: int = 0
    question: str = ""
    answer: str = ""
    combined_content: str = ""
    created_at: datetime = datetime.now()
    version: str = ""

class Paper_RawData(BaseModel):
    id: int = 0
    document_name: str = ""
    page_number: int = 0
    chunk_index: int = 0
    chunk_content: str = ""
    created_at: datetime = datetime.now()
    version: str = ""