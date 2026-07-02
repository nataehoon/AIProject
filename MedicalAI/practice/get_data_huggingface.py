from datasets import load_dataset

def get_qa_data():
    print("허깅페이스 서버에서 의학 데이터셋(QA) 다운로드를 시작합니다...")
    dataset = load_dataset("lavita/MedQuAD", split="train[:100]")
    print("다운로드 및 캐싱이 완료되었습니다!\n")

    print("=== 데이터셋 구조 확인 ===")
    print(dataset)
    print("-" * 50)

    first_row = dataset[0]

    print("=== 0번째 의학 데이터 상세 내용 ===")
    print(f"의학 질문:\n{first_row['question']}\n")
    print(f"전문의 답변:\n{first_row['answer']}\n")
    print("-" * 50)

    print("=== RAG 가공을 위한 전체 데이터 순회 예시 ===")
    for index, row in enumerate(dataset):
        combined_text = f"질문: {row['question']} 답변: {row['answer']}"
        if index <3:
            print(f"[{index + 1}번 가공 데이터]: {combined_text[:200]}...")

def get_paper_data():
    print("허깅페이스 서버에서 의학 데이터셋(Paper) 다운로드를 시작합니다...")
    dataset = load_dataset("ahmedabdelwahed/Medical_papers_title_and_abstract_NLP_dataset", split="train[:20]")
    print("다운로드 및 캐싱이 완료되었습니다!\n")

    print("=== 데이터셋 구조 확인 ===")
    print(dataset)
    print("-" * 50)

    first_row = dataset[0]
    
    print("=== 0번째 의학 데이터 상세 내용 ===")
    print(f"논문 제목:\n{first_row['title']}\n")
    print(f"논문 초록:\n{first_row['abstract']}\n")
    print("-" * 50)

    print("=== RAG 가공을 위한 전체 데이터 순회 예시 ===")
    for index, row in enumerate(dataset):
        combined_text = f"제목: {row['title']} 초록: {row['abstract']}"
        if index <3:
            print(f"[{index + 1}번 가공 데이터]: {combined_text[:200]}...")

def main():
    search_data = input("조회할 데이터를 입력하세요 (1: QA, 2: Paper)\n입력: ")

    if search_data == "1":
        get_qa_data()
    elif search_data == "2":
        get_paper_data()


if __name__ == "__main__":
    main()