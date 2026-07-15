from sentence_transformers import SentenceTransformer
import numpy as np
from config import DEFAULT_EMBEDDING_MODEL

_embedding_model = SentenceTransformer(DEFAULT_EMBEDDING_MODEL)

def encode(raw_data: str):
    embeddings = _embedding_model.encode(raw_data, convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)

    return embeddings.tolist()

def list_encode(raw_data: list[str]):
    embeddings = _embedding_model.encode(raw_data, convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)

    return embeddings.tolist()