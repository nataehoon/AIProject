import os

VLM_API_URL = "https://overrate-comprised-outfield.ngrok-free.dev/v1/transformers/chat/completions"
VLM_NUM_PREDICT = 8192
VLM_NUM_CTX = 32768
VLM_MAX_TOKEN = 2048
VLM_MODEL = "google/medgemma-4b-it"
VLM_THINK = False

LLM_API_URL = "https://overrate-comprised-outfield.ngrok-free.dev/v1/transformers/chat/completions"
LLM_NUM_PREDICT = 8192
LLM_NUM_CTX = 8192
LLM_MAX_TOKEN = 2048
LLM_MODEL = "google/medgemma-4b-it"
LLM_THINK = True

ROUTER_LLM_API_URL = "https://overrate-comprised-outfield.ngrok-free.dev/v1/transformers/chat/completions"
ROUTER_NUM_PREDICT = 1024
ROUTER_NUM_CTX = 2048
ROUTER_MAX_TOKEN = 2048
ROUTER_MODEL = "google/medgemma-4b-it"
ROUTER_THINK = False

DEFAULT_TEMPERATURE = 0.0

DEFAULT_EMBEDDING_MODEL = "BM-K/KoSimCSE-roberta-multitask"
QA_DATASET_MODEL = "lavita/MedQuAD"
PAPER_DATASET_MODEL = "ahmedabdelwahed/Medical_papers_title_and_abstract_NLP_dataset"

RAG_SIMILARITY = "0.75"

CLASSIFICATION_API_URL = "https://overrate-comprised-outfield.ngrok-free.dev/predict"