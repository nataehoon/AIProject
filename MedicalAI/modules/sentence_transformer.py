from sentence_transformers import SentenceTransformer
import numpy as np
from config import DEFAULT_EMBEDDING_MODEL

def get_vector_data(raw_data: list[str]):
    embedding_model = SentenceTransformer(DEFAULT_EMBEDDING_MODEL)

    embeddings = embedding_model.encode(raw_data)

    v_list = []
    for index, data in enumerate(raw_data):
        v_data = np.array(embeddings[index], dtype=np.float32).tolist()
        v_list.append(v_data)
    return v_list