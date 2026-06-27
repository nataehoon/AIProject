from pydantic import BaseModel

class chat(BaseModel):
    role: str
    content: str
    model_used: str