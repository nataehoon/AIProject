from pydantic import BaseModel

class GetPaperDataRequestDTO(BaseModel):
    url: str
    key_word: str
    paper_count: int
    remote_url: str
    