from modules.db_repository import execute_select_query, execute_non_query, execute_transaction_query
from models.mediinfo import Mediinfo, VersionInfo, QA_RawData, Paper_RawData
from datetime import datetime
from modules.sentence_transformer import encode, list_encode
from datasets import load_dataset
from config import QA_DATASET_MODEL, PAPER_DATASET_MODEL

class MedicalService:
    @staticmethod
    def get_my_mediinfo(id: int) -> list["Mediinfo"] | None:
        qeury = "SELECT * FROM mediinfo WHERE member_id=%s"
        params = (id,)

        raw_rows = execute_select_query(query=qeury, params=params)

        if not raw_rows:
            return None

        return [Mediinfo(**row) for row in raw_rows]

    @staticmethod
    def save_my_mediinfo(my_medi: Mediinfo) -> bool | None:
        query = "INSERT INTO mediinfo(member_id, modality, file_name, analyzed_text, body_part) VALUES(%s, %s, %s, %s, %s);"
        params = (my_medi.member_id, my_medi.modality, my_medi.file_name, my_medi.analyzed_text, my_medi.body_part)

        return execute_non_query(query, params)

    @staticmethod
    def get_version_info() -> list["VersionInfo"] | None:
        query = "SELECT * FROM prod_version_info"

        raw_rows = execute_select_query(query)

        if not raw_rows:
            return None

        return [VersionInfo(**row) for row in raw_rows]

    @staticmethod
    def get_raw_data() -> tuple[list[QA_RawData], list[Paper_RawData]] | None:
        query = "SELECT * FROM medical_qa_knowledge_staging ORDER BY CAST(version AS DATE) DESC;"
        qa_raw_rows = execute_select_query(query)
        if qa_raw_rows:
            qa_raw_list = [QA_RawData(**row) for row in qa_raw_rows]
        else:
            qa_raw_list = []

        query = "SELECT * FROM medical_paper_chunks_staging ORDER BY CAST(version AS DATE) DESC;"
        paper_raw_rows = execute_select_query(query)
        if paper_raw_rows:
            paper_raw_list = [Paper_RawData(**row) for row in paper_raw_rows]
        else:
            paper_raw_list = []

        return (qa_raw_list, paper_raw_list)

    @staticmethod
    def save_version_select(version: str):
        query = "INSERT INTO prod_version_info(version, active) VALUES(%s, %s) ON CONFLICT (version) DO UPDATE SET active = EXCLUDED.active"
        params = (version, True)

        result = execute_non_query(query, params)

        if result > 0:
            query = "UPDATE prod_version_info SET active = %s WHERE version != %s"
            params = (False, version)

            execute_non_query(query, params)

            query = "INSERT INTO medical_qa_knowledge_prod(question, answer, combined_content, specialty, embedding, create_at, version_id) " \
            "SELECT question, answer, combined_content, specialty, embedding, CURRENT_TIMESTAMP as create_at, (SELECT id FROM prod_version_info WHERE version = %s" \
                    ") as version_id from medical_qa_knowledge_staging WHERE version = %s"
            params = (version, version)

            execute_non_query(query, params)

            query = "INSERT INTO medical_paper_chunks_prod(document_name, page_number, chunk_index, chunk_content, embedding, create_at, version_id) " \
            "SELECT document_name, page_number, chunk_index, chunk_content, embedding, CURRENT_TIMESTAMP as create_at, (SELECT id FROM prod_version_info WHERE version = %s" \
                    ") as version_id from medical_paper_chunks_staging WHERE version = %s"
            params = (version, version)
            
            execute_non_query(query, params)

    @staticmethod
    def run_rag_pipeline():
        yield 1
        qa_dataset = load_dataset(QA_DATASET_MODEL, split="train[:200]")

        yield 2
        try:
            qa_texts = []
            for row in qa_dataset:
                question = row.get("question") or ""
                answer = row.get("answer") or ""
                if not question or not answer:
                    continue
                combined = f"Medical Question: {question.strip()}\nExpert Answer: {answer.strip()}"
                qa_texts.append(combined)

            qa_v_list = list_encode(qa_texts)
        except Exception as e:
            print(f"Q&A 전처리 error: {e}")

        yield 3
        now = datetime.now().strftime("%Y-%m-%d")
        qa_queries_and_params = []
        cleanup_query = "DELETE FROM medical_qa_knowledge_staging WHERE version = %s"
        cleanup_params = (now,)
        qa_queries_and_params.append((cleanup_query, cleanup_params))

        qa_query = "INSERT INTO medical_qa_knowledge_staging(question, answer, combined_content, specialty, embedding, version) VALUES(%s, %s, %s, %s, %s, %s);"
        for index, row in enumerate(qa_dataset):
            qa_param = (row['question'], row['answer'], qa_texts[index], "General", qa_v_list[index], now)
            qa_queries_and_params.append((qa_query, qa_param))

        qa_fifo_query = "DELETE FROM medical_qa_knowledge_staging WHERE version NOT IN (SELECT version FROM (SELECT DISTINCT version FROM medical_qa_knowledge_staging ORDER BY version DESC LIMIT 3) AS tmp);"
        qa_queries_and_params.append((qa_fifo_query, ()))

        execute_transaction_query(qa_queries_and_params)

        yield 4
        paper_dataset = load_dataset(PAPER_DATASET_MODEL, split="train[:200]")

        yield 5
        try:
            paper_chunks_data = []
            for paper in paper_dataset:
                title = paper["title"]
                abstract = paper["abstract"]

                page_num = 0
                chunk_size = 1000
                for start_idx in range(0, len(abstract), chunk_size):
                    page_num += 1
                    chunk_str = abstract[start_idx: start_idx + chunk_size]
                    paper_chunks_data.append({"title": title, "content": chunk_str, "page_num": page_num})

            chunk_texts = [item["content"] for item in paper_chunks_data]
            paper_v_list = list_encode(chunk_texts)
        except Exception as e:
            print(f"paper 전처리 error: {e}")

        yield 6
        paper_queries_and_params = []
        paper_clean_query = "DELETE FROM medical_paper_chunks_staging WHERE version = %s"
        paper_clean_param = (now,)
        paper_queries_and_params.append((paper_clean_query, paper_clean_param))

        paper_query = "INSERT INTO medical_paper_chunks_staging(document_name, page_number, chunk_index, chunk_content, embedding, version) VALUES(%s, %s, %s, %s, %s, %s);"
        for index, item in enumerate(paper_chunks_data):
            paper_params = (item["title"], item["page_num"], index, item["content"], paper_v_list[index], now)
            paper_queries_and_params.append((paper_query, paper_params))

        paper_fifo_query = "DELETE FROM medical_paper_chunks_staging WHERE version NOT IN (SELECT version FROM (SELECT DISTINCT version FROM medical_paper_chunks_staging ORDER BY version DESC LIMIT 3) AS tmp);"
        paper_queries_and_params.append((paper_fifo_query, ()))

        execute_transaction_query(paper_queries_and_params)
        yield 7