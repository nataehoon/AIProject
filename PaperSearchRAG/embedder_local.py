import os
import torch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

def initializze_local_embedder():
    print("[하드웨어 분석] GPU 장치 스캔 시작...")

    # [하드웨어 가속 판정]
    if torch.cuda.is_available():
        device = "cuda"
        print("엔진이 활성화 되었습니다.")
    else:
        device = "cpu"
        print("CUDA를 찾을 수 없어 CPU 연단 모드로 전환합니다.")

    # [모델 선정] 하드웨어 성능에 맞는 모델 선정
    model_name = "BAAI/bge-small-en-v1.5"

    # 모델이 구동될 때 주입할 하드웨어 디바이스 매핑 인자 조립
    encode_kwargs = {'normalize_embeddings': True} # 코사인 유사도 연산 속도를 높이기 위한 정규화 옵션
    model_kwargs = {'device': device}

    print(f"허깅페이스에서 '{model_name}' 모델 로드 및 GPU 컨텍스트 바인딩 중...")

    embeddings_engine = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

    print("임베딩 모델 레이어 가동 준비 완료.")
    return embeddings_engine

sample_chunks = [
    "Retrieval-Augmented Generation (RAG) improves LLM responses by fetching relevant documents.",
    "PostgreSQL with pgvector extension allows high-performance vector similarity search.",
    "NVIDIA MX450 GPU supports CUDA, which accelerates embedding generation pipelines."
]

def main():
    """임베딩 컴포넌트 단위 테스트 진입점"""
    # 1. 하드웨어 바인딩된 입베딩 엔진 획득
    embedder = initializze_local_embedder()

    print("\n 테스트 텍스트 청크 벡터화(Embedding) 변환 가동...")

    # 2. 실제 텍스트 배열을 찔러서 고차원 실수 배열(벡터)로 변환
    vector_results = embedder.embed_documents(sample_chunks)

    print(f"[완료] 변환된 벡터 개수: {len(vector_results)}개")
    print(f"[완료] 임베딩 차원 수: {len(vector_results[0])}차원 (bge-small 기본 스펙)")
    print(f"첫 번째 청크의 벡터 스냅샷: {vector_results[0][:5]} ... [생략]")

if __name__ == "__main__":
    main()