import os

OLLAMA_VLM_API_URL = "https://overrate-comprised-outfield.ngrok-free.dev/v1/image/completions"
VLM_NUM_PREDICT = 8192
VLM_NUM_CTX = 32768
VLM_MODEL = "qwen3-vl:8b-instruct"
VLM_THINK = False

OLLAMA_LLM_API_URL = "https://overrate-comprised-outfield.ngrok-free.dev/v1/image/completions"
LLM_NUM_PREDICT = 8192
LLM_NUM_CTX = 8192
LLM_MODEL = "qwen3-vl:8b-instruct"
LLM_THINK = True

DEFAULT_TEMPERATURE = 0.0

DEFAULT_EMBEDDING_MODEL = "BM-K/KoSimCSE-roberta-multitask"
QA_DATASET_MODEL = "lavita/MedQuAD"
PAPER_DATASET_MODEL = "ahmedabdelwahed/Medical_papers_title_and_abstract_NLP_dataset"