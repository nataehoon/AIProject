import os
from datasets import load_dataset

# [경로 설정] 파싱 완료된 텍스트 파일들을 저장할 상대 경로 지정
TEXT_DIR = "./extracted_texts"
os.makedirs(TEXT_DIR, exist_ok=True)

def download_papers_from_huggingface(keyword: str, max_results: int = 5):
    """arXiv API가 다운되었을 때 대안으로 사용하는 허길페이스 기반 논문 수집 함수"""
    print(f"arXiv API 우회 진행: 허길페이스에서 '{keyword}' 관련 논문 수집 중...")

    try:
        # [데이터셋 원격 로드] arXiv 논문 약 200만 개가 텍스트화되어 저장된 공용 저장소에서 스트리밍 모드로 데이터를 켭니다.
        #dataset = load_dataset("Exalabs/arxiv-papers", split="train", streaming=True)
        dataset = load_dataset("CShorten/ML-ArXiv-Papers", split="train", streaming=True)

        saved_count = 0

        # [반복문] 데이터셋 스트림에서 논문을 한 편씩 써내어 순회 검사
        for paper in dataset:
            if saved_count >= max_results:
                break

            title = paper.get("title", "")
            abstract = paper.get("abstract", "")
            #full_text = paper.get("full_text", "")

            print(f"keys: {list(paper.keys())}")
            print(f"title: {title}")
            print(f"abstract: {abstract}")

            # 사용자가 찾는 키워드(예: Retrieval-Augmented Generation)가 논문 제목이나 초록에 대소문자 구분 없이 포함되어 있는지 검사
            if (keyword.lower() in title.lower()) or (keyword.lower() in abstract.lower() or ("rag" in title.lower()) or ("rag" in abstract.lower())):
                # 윈도우 파일 시스템에 저장할 수 있도록 논문 제목의 특수문자 정제 수행
                safe_title = "".join([c for c in title if c.isalnum() or c in "._-"]).strip()
                txt_filename = f"{safe_title}.txt"
                txt_path = os.path.join(TEXT_DIR, txt_filename)

                # [파일 저장] PDF 스트림을 파싱할 필요 없이 바로 텍스트를 정형화하여 디스크에 기록
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(f"========================================================\n")
                    f.write(f"Title: {title}\n")
                    f.write(f"========================================================\n\n")
                    f.write(f"--- Abstract ---\n {abstract}\n\n")
                    #f.write(f"--- FULL TEXT ---\n {full_text}\n")

                    print(f"[우회 수집 완료] {saved_count + 1}: {safe_title}.txt")
                    saved_count += 1

            print(f"우회 수집 파이프라인 정상 종료. 총 {saved_count}개의 최신 논문 텍스트 확보 완료.")

    except Exception as e:
        print(f"허깅페이스 데이터 로드 중 예상치 못한 에러 발생: {e}")

def main():
    """우회 파이프라인 가동 메인 진입점"""
    search_keyword = "Retrieval-Augmented Generation"

    # 외부 API 이슈에서 완전히 독립되어 5개의 핵심 RAG 논문 텍스트를 즉시 수집합니다
    download_papers_from_huggingface(keyword=search_keyword, max_results=5)

if __name__ == "__main__":
    main()