import os
import time
import arxiv
import fitz #PyMuPDF 라이브러리
import pathlib
from urllib.request import urlretrieve  # 원격 웹 URL에서 파일을 직접 다운로드하여 디스크에 저장하는 파이썬 표준 함수

#1. 파일 및 폴더 경로 설정 (상대 경로)
DOWNLOAD_DIR = "./downloads"
TEXT_DIR = "./extracted_texts"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(TEXT_DIR, exist_ok=True)

def search_and_download_papers(query: str, max_results: int =3):
    """arXiv API를 통해 논문을 검색하고 PDF를 다운로드합니다."""
    print(f"arXiv API를 통해 '{query}' 주제의 논문을 검색하는 중...")

    # 검색 조건 설정
    search = arxiv.Search(
        query= query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )

    # API를 호풀할 클라이언트 객체를 생성
    client = arxiv.Client(page_size=20, delay_seconds=3.0, num_retries=5)

    downloaded_files = []

    try:
        # 클라이언트에 search 조건을 인자로 던져 결과 루프
        for result in client.results(search):
            print(f"\n📥 논문 수집 대상 발견: {result.title}")
            
            try:
                
                #파일명으로 쓸 수 없게 특수문자가 들어간 경우를 대비해 타이틀 정제
                save_title = "".join([c for c in result.title if c.isalnum() or c in "._- "]).strip()
                if len(save_title) > 50:
                    save_title = save_title[:50]

                filename = save_title + ".pdf"

                pdf_path = pathlib.Path(DOWNLOAD_DIR, filename)

                if not pdf_path.exists():
                    print(f" [신규 파일 발견]: {filename}")
                    
                    # [4.0.0 핵심 우회 매커니즘]
                    # 삭제된 download_pdf 메서드 대신, result 객체가 보장하는 pdf_url 스트링 주소를 추출합니다.
                    # C#의 WebClient.DownloadFile(url, path)과 완전히 같은 원리로 직접 원천 다운로드를 수행합니다.
                    download_url = result.pdf_url
                    print(f"🔗 원본 PDF 링크 확인: {download_url}")
                    print(f"⏳ 원격 다운로드 파이프라인 가동 중...")
                    
                    urlretrieve(download_url, pdf_path)
                    print(f"   [성공] PDF 로컬 안착 완료: {pdf_path}")

                    # 성공 리스트에 추가
                    downloaded_files.append((save_title, pdf_path))

                    # 연속적인 커넥션 요청으로 인한 HTTP 429(Too Many Requests) 차단을 방어하기 위해 3초간 대기
                    time.sleep(3.0)

            except Exception as e:
                print(f"   ❌ '{result.title}' 다운로드 중 예외 발생: {e}")
                continue

    except arxiv.HTTPError as e:
        if "429" in str(e):
            print("arXiv 서버의 임시 IP 차단(HTTP 429)이 아직 유지 중입니다.")
            print("약 5~10분 정도 컴퓨터를 쉬게하거나, 인터넷 연결을 재접속(IP 변경)한 뒤 다시 실행해 주세요.")
        raise e

    return downloaded_files

def extract_text_from_pdf(pdf_path: str, output_txt_path: str):
    """PyMuPDF(fitz)를 사용하여 로컬 PDF 파일을 열고 내부의 텍스트를 파싱하여 .txt로 저장하는 함수"""
    doc = fitz.open(pdf_path)
    full_text = ""

    # PDF의 총 페이지 수(len(doc))만큼 인덱스를 돌며 한 페이지씩 접근
    for page_num in range(len(doc)):
        page = doc.load_page(page_num) # 문서 객체로부터 해당 페이지 번호의 데이터를 로드

        # 해당 페이지 내에 물리적으로 배치된 텍스트들을 순수 문자열 스트링으로 추출하여 누적
        full_text += page.get_text()

        # RAG 시스템이 나중에 문맥을 파악할 때 도움을 주도록 페이지 구분선 메타데이터를 강제로 주입
        full_text += f"\n--- PAGE {page_num +1} ---\n"

    # [파일 입출력] 파싱이 완료된 텍스트를 외장 SSD 내의 지정된 경로에 .txt 파일로 기록
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    print(f"순수 텍스트 파싱 및 파일 저장 완료: {output_txt_path}")

def main():
    """PaperSearchRAG의 수집 파이프라인을 구동하는 메인 진입 함수"""
    # 우리 RAG 시스템의 기반이 될 기술 도메인 논문 검색 키워드 설정
    search_keyword = "Retrieval-Augmented Generation"

    # arXiv API를 찔러 조건에 맞는 논문 max_results개를 다운로드 폴더에 저장하고 리스트를 받아옴
    papers = search_and_download_papers(query=search_keyword, max_results=10)

    # 다운로드 목록 리스트를 순화하며 각각의 PDF를 .txt 파일로 파싱 및 덤프
    for title, pdf_path in papers:
        # 추출될 텍스트 파일의 전체 저장 경로를 OS 규격에 맞게 조립(extracted_texts/논문제목.txt)
        txt_path = os.path.join(TEXT_DIR, f"{title}.txt")

        # 실제 텍스트 추출 함수 실행
        extract_text_from_pdf(pdf_path, txt_path)

if __name__ == "__main__":
    main()