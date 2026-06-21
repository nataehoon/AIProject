import os
import pathlib
import re
import requests
from langchain_text_splitters import RecursiveCharacterTextSplitter

import db_repository

TEXT_DIR = "./extracted_texts"
REMOTE_GPU_URL = "https://overrate-comprised-outfield.ngrok-free.dev/embed"

def process_and_chunk_papers_hybrid():
    """로컬 파일을 파싱한 후 문장 벡터화 연산만 원격 고성능 GPU 서버에 REST API로 위임하는 핵심 함수"""

    # 1. 의미 단위 문장 분할기(chunk) 세팅 - 가벼운 스트링 슬라이싱이므로 로컬 CPU가 처리
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    dir_path = pathlib.Path(TEXT_DIR)

    # [가드 코드] 읽어올 타겟 텍스트 소스가 물리적으로 존재하는지 무결성 체크
    if not dir_path.exists() or not any(dir_path.iterdir()):
        print(f"논문 파일이 존재하지 않습니다.")
        return

    print(f"[하이브리드 엔진 부팅] 로컬 I/O 스캔 및 원격 클라우드 GPU 연산 라우팅 가동...")

    global_batch_queue = []
    page_pattern = re.compile(r"^--- PAGE (\d+) ---")

    for txt_file in dir_path.iterdir():
        if txt_file.is_file() and txt_file.suffix == ".txt":
            print(f"\n [파일 파싱 가동] 파일명: {txt_file.name}")

            current_page = 1
            page_text_buffer = ""

            with open(txt_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in lines:
                clean_line = line.strip()

                match = page_pattern.match(clean_line)

                if match:
                    if page_text_buffer.strip():
                        chunks = text_splitter.split_text(page_text_buffer)

                        if chunks:
                            print(f"[원격 GPU 연산] {txt_file.name} / {current_page}페이지의 {len(chunks)}개 청크 송신...")

                            try:
                                response = requests.post(REMOTE_GPU_URL, json={"chunks": chunks})

                                if response.status_code == 200:
                                    chunk_vectors = response.json().get("vectors", [])

                                    for raw_text, original_vector in zip(chunks, chunk_vectors):
                                        standard_1536_vector = db_repository.pad_vector_to_1536(original_vector)

                                        paper_entity = db_repository.ChunkedPaperEntity(
                                            title=txt_file.name.replace(".txt", ""),
                                            page_number=current_page,
                                            paragraph_text=raw_text,
                                            embedding_vector=standard_1536_vector
                                        )
                                        global_batch_queue.append(paper_entity)
                                else:
                                    # 💡 200이 아니라 500이나 404 에러 HTML이 내려온 경우, 예외를 터트리지 않고 진짜 원인을 출력합니다.
                                    print(f"[서버 에러] 구글 코랩 서버가 응답 실패를 리턴했습니다. 상태 코드: {response.status_code}")
                                    print(f"[서버 에러 본문 스냅샷]: {response.text[:200]}")  # 앞글자 200자만 덤프하여 에러 원인 분석
                                    print(f"팁: 코랩 웹페이지 로그 창을 열어 'Out of Memory'나 다른 파이썬 예외가 터졌는지 확인하세요.")

                            except Exception as e:
                                print(f"원격 GPU 임베딩 가속 통신 실패 스킵: {e}")
                    current_page = int(match.group(1))
                    page_text_buffer = ""

                else:
                    page_text_buffer += line + "\n"

            if page_text_buffer.strip():
                chunks = text_splitter.split_text(page_text_buffer)

                if chunks:
                    print(f"[최종 페이지 연산] {txt_file.name} / {current_page}페이지의 {len(chunks)}개 청크 송신...")
                    try:
                        response = requests.post(REMOTE_GPU_URL, json={"chunks": chunks})

                        if response.status_code == 200:
                            chunk_vectors = response.json().get("vectors", [])

                            for raw_text, original_vector in zip(chunks, chunk_vectors):
                                standard_1536_vector = db_repository.pad_vector_to_1536(original_vector)
                                paper_entity = db_repository.ChunkedPaperEntity(
                                    title=txt_file.name.replace(".txt", ""),
                                    page_number=current_page,
                                    paragraph_text=raw_text,
                                    embedding_vector=standard_1536_vector
                                )
                                global_batch_queue.append(paper_entity)
                        else:
                            # 💡 200이 아니라 500이나 404 에러 HTML이 내려온 경우, 예외를 터트리지 않고 진짜 원인을 출력합니다.
                            print(f"      ❌ [서버 에러] 구글 코랩 서버가 응답 실패를 리턴했습니다. 상태 코드: {response.status_code}")
                            print(f"      📝 [서버 에러 본문 스냅샷]: {response.text[:200]}")  # 앞글자 200자만 덤프하여 에러 원인 분석
                            print(f"      💡 팁: 코랩 웹페이지 로그 창을 열어 'Out of Memory'나 다른 파이썬 예외가 터졌는지 확인하세요.")
                    except Exception as e:
                        print(f"최종 페이지 통신 예외 스킵: {e}")

    # [최종 적재 레이어] 파일 순회가 모두 완료되어 완벽한 페이지 정보와 벡터가 결합된 전역 큐를 DB에 단 1번 찌릅니다.
    print("\n--- 🏁 전역 파일 컴파일 및 하이브리드 GPU 연산 완료 ---")
    print(f"📦 총 {len(global_batch_queue)}개의 동적 페이지 매핑 엔티티가 준비되었습니다.")
    
    # 🗄️ 단 1번의 데이터베이스 커넥션 오픈으로 영구 일괄 저장 실행
    db_repository.bulk_insert_paper_chunks(global_batch_queue)

    # [로컬 디렉토리 순회] 하드디스크의 텍스트 파일 리스트를 한 개씩 스트리밍 로드
    # for txt_file in dir_path.iterdir():
    #     if txt_file.is_file() and txt_file.suffix == ".txt":
    #         print(f"[로컬 I/O 파일 인식] {count}번째 파일 읽는 중: {txt_file.name}")
    #         count += 1

    #         with open(txt_file, "r", encoding="utf-8") as f:
    #             raw_paper_content = f.read()

    #         # 의미 단위 분할 실행 => 로클 메모리에 문자열 배열 생성
    #         chunks = text_splitter.split_text(raw_paper_content)
    #         print(f"청킹 분할 성공: 로컬 영역에 {len(chunks)}개의 의미론적 데이터 조각 팩 추출")
    #         print(f"[네트워크 요청] GPU 서버로 {len(chunks)}개의 청크 데이터 송신 중...")

    #         try:
    #             response = requests.post(REMOTE_GPU_URL, json={"chunks": chunks})

    #             result_data = response.json()
    #             chunk_vectors = result_data.get("vectors", [])
    #             print(f"[원격 연산 완료] GPU 코어가 계산한 벡터 {len(chunk_vectors)}개 수신 성공")

    #             for index, (raw_text, original_vector) in enumerate(zip(chunks, chunk_vectors)):
    #                 standard_1536_vector = db_repository.pad_vector_to_1536(original_vector)

    #                 record_dto = (
    #                     txt_file.name.replace(".txt", ""), # title
    #                     1,                                 # page_number
    #                     raw_text,                          # paragraph_text
    #                     standard_1536_vector               # embedding_vector
    #                 )

    #             print(f" - 생성된 벡터 차원: {len(chunk_vectors[0])}차원 (bge-small 스펙 일치)")
    #             print(f" - 첫 번째 수신 데이터 스냅샷: {chunk_vectors[0][:3]}... [검증 성공]")

    #         except Exception as e:
    #             continue

def main():
    """원래의 프로젝트 디렉토리 아키텍처를 100% 보존한 하이브리드 가속 진입점"""
    process_and_chunk_papers_hybrid()

if __name__ == "__main__":
    main()