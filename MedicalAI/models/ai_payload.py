from pydantic import BaseModel
from typing import Any, List, Dict

class OllamaPayload(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    temperature: float
    think: bool
    stream: bool
    options: Dict[str, Any] = {}
