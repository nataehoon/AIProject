from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import db_repository
import embedder_colab
import downloader_arxiv
from models.get_paper_dto import GetPaperDataRequestDTO

app = FastAPI(
    title="논문 데이터 수집 및 가속화 인덱싱 엔진",
    description="논문 데이터 수집 후 텍스트화하고, 임베딩 모델을 통해 벡터화하여 db에 저장",
    version="1.0.0"
)

@app.post(
    "/api/getpaper",
    summary="arXiv 최신 논문 실시간 검색 및 중복제외 벌트 인서트 집행",
    tags=["RAG 데이터 수집 및 적재 컨트롤러"]
)
