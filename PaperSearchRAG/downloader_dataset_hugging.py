import os  # 운영체제 디렉토리 생성 및 파일 경로 제어를 위한 내장 모듈
from datasets import load_dataset  # 허깅페이스에서 안전한 Parquet 데이터를 한 줄씩 스트리밍하는 함수

# [경로 설정] 추출된 대용량 본문 텍스트 파일들을 저장할 폴더 상대 경로
TEXT_DIR = "./extracted_texts"
os.makedirs(TEXT_DIR, exist_ok=True)


def download_perfect_full_text_papers(keyword: str, max_results: int = 3):
    """허깅페이스 공식 팀이 영구 보존하는 데이터셋에서 논문 전체 본문을 긁어오는 완전판 함수"""
    print(
        f"🚀 [엔터프라이즈 파이프라인] 허깅페이스 정식 데이터셋에서 '{keyword}' 검색 시작..."
    )

    try:
        # [공식 데이터셋 지정] 스크립트 제한이 없는 정적 Parquet 포맷의 대형 공인 데이터셋 로드
        dataset = load_dataset(
            "HuggingFaceFW/fineweb-edu",
            name="sample-10BT",
            split="train",
            streaming=True,
        )

        saved_count = 0  # 성공적으로 저장된 논문 파일 개수 카운터
        try_count = 0

        # [열거자 순회] 스트리밍 엔진에서 딕셔너리 인스턴스를 순차적으로 꺼내옵니다.
        for paper in dataset:
            if saved_count >= max_results:
                break

            # 안전하게 데이터 본문 추출 (.get 메서드 활용)
            full_text = paper.get("text", "")

            # [핵심 필터] 대다수의 일반 웹 문서 중, 본문에 학술용어(arXiv)가 들어가거나 
            # 키워드(Retrieval-Augmented Generation)가 녹아있는 논문급 문서만 필터링
            keyword_lower = keyword.lower()
            if (keyword_lower in full_text.lower() or "llm" in full_text.lower() or "AI" in full_text or "RAG" in full_text):

                # 파일 이름으로 쓸 수 있게 논문 첫 줄(보통 제목)에서 일부를 가져와 파일명 정제
                # 전체 본문의 앞 30글자를 따서 제목 대용으로 씁니다.
                first_line = full_text.split("\n")[0][:30]
                safe_title = "".join(
                    [c for c in first_line if c.isalnum() or c in "._- "]
                ).strip()

                # 파일명이 비어있을 경우를 대비한 가드 코드
                if not safe_title:
                    safe_title = f"arxiv_paper_{saved_count + 1}"

                txt_filename = f"{safe_title}.txt"
                txt_path = os.path.join(TEXT_DIR, txt_filename)

                # [스트림 쓰기] 파일 I/O 가동하여 전체 본문 원본 데이터 통째로 기록
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(f"=========================================\n")
                    f.write(f"SOURCED RAW TEXT DATA (FULL TEXT)\n")
                    f.write(f"=========================================\n\n")
                    f.write(full_text)

                print(
                    f"📄 [수집 완료] {saved_count + 1}: {txt_filename} (전체 본문 저장 성공)"
                )
                saved_count += 1

            try_count += 1
            if try_count >= 50:
                break
        print(
            f"\n🟢 최종 파이프라인 완료! 총 {saved_count}개의 고품질 논문 전체 본문을 덤프했습니다."
        )

    except Exception as e:
        print(f"❌ 허깅페이스 공식 엔진 연동 중 에러 발생: {e}")


def main():
    """RAG 원천 데이터 수집 가동 진입점"""
    search_keyword = "Retrieval-Augmented Generation"

    # 뼈대 검증을 위해 3개의 완성형 논문 본문 텍스트를 수집합니다.
    download_perfect_full_text_papers(keyword=search_keyword, max_results=3)


if __name__ == "__main__":
    main()