from pydantic import BaseModel
from typing import Any, List, Dict

class AI_Payload(BaseModel):
    model: str
    messages: List[Dict[str, Any]]
    temperature: float
    think: bool
    stream: bool
    num_predict: int
    num_ctx: int
    max_tokens: int
