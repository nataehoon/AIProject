from modules.db_repository import execute_select_query, execute_non_query, execute_transaction_query
from models.mediinfo import Mediinfo
from datetime import datetime
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from datasets import load_dataset
import numpy as np
from config import DEFAULT_EMBEDDING_MODEL

load_dotenv()

class MedicalService:
    @staticmethod
    def get_my_mediinfo(id: int) -> Mediinfo | None:
        qeury = "SELECT * FROM mediinfo WHERE id=%s"
        params = (id,)

        raw_rows = execute_select_query(query=qeury, params=params)

        if not raw_rows:
            return None

        return Mediinfo(**raw_rows[0])

    @staticmethod
    def save_my_mediinfo(my_medi: Mediinfo) -> bool | None:
        query = "INSERT INTO mediinfo(member_id, modality, file_name, analyzed_text) VALUES(%s, %s, %s, %s);"
        params = (my_medi.member_id, my_medi.modality, my_medi.file_name, my_medi.analyzed_text)

        return execute_non_query(query, params)

    @staticmethod
    def run_rag_pipeline():
        yield 1
        embedding_model = SentenceTransformer(DEFAULT_EMBEDDING_MODEL)

        qa_dataset = load_dataset("lavita/MedQuAD", split="train[:50]")

        yield 2
        qa_texts = []
        for row in qa_dataset:
            combined = f"Medical Question: {row['question'].strip()}\nExpert Answer: {row['answer'].strip()}"
            qa_texts.append(combined)

        qa_embeddings = embedding_model.encode(qa_texts)

        yield 3
        now = datetime.now().strftime("%Y-%m-%d")
        qa_queries_and_params = []
        cleanup_query = "DELETE FROM medical_qa_knowledge_staging WHERE version = %s"
        cleanup_params = (now,)
        qa_queries_and_params.append((cleanup_query, cleanup_params))

        qa_query = "INSERT INTO medical_qa_knowledge_staging(question, answer, combined_content, specialty, embedding, version) VALUES(%s, %s, %s, %s, %s, %s);"
        qa_params = []
        for index, row in enumerate(qa_dataset):
            v_data = np.array(qa_embeddings[index], dtype=np.float32).tolist()
            qa_param = (row['question'], row['answer'], qa_texts[index], "General", v_data, now)
            qa_queries_and_params.append((qa_query, qa_param))

        qa_fifo_query = "DELETE FROM medical_qa_knowledge_staging WHERE version NOT IN (SELECT version FROM (SELECT DISTINCT version FROM medical_qa_knowledge_staging ORDER BY version DESC LIMIT 3) AS tmp);"
        qa_queries_and_params.append((qa_fifo_query, ()))

        execute_transaction_query(qa_queries_and_params)

        yield 4
        paper_dataset = load_dataset("ahmedabdelwahed/Medical_papers_title_and_abstract_NLP_dataset", split="train[:50]")

        yield 5
        paper_chunks_data = []
        for idx, paper in enumerate(paper_dataset):
            title = paper["title"]
            abstract = paper["abstract"]


            chunk_size = 1000
            for start_idx in range(0, len(abstract), chunk_size):
                chunk_str = abstract[start_idx: start_idx + chunk_size]
                paper_chunks_data.append({"title": title, "content": chunk_str})

        chunk_texts = [item["content"] for item in paper_chunks_data]
        paper_embeddings = embedding_model.encode(chunk_texts)

        yield 6
        paper_queries_and_params = []
        paper_clean_query = "DELETE FROM medical_paper_chunks_staging WHERE version = %s"
        paper_clean_param = (now,)
        paper_queries_and_params.append((paper_clean_query, paper_clean_param))

        paper_query = "INSERT INTO medical_paper_chunks_staging(document_name, page_number, chunk_index, chunk_content, embedding, version) VALUES(%s, %s, %s, %s, %s, %s);"
        for index, item in enumerate(paper_chunks_data):
            v_data = np.array(paper_embeddings[index], dtype=np.float32).tolist()
            paper_params = (item["title"], 1, index, item["content"], v_data, now)
            paper_queries_and_params.append((paper_query, paper_params))

        paper_fifo_query = "DELETE FROM medical_paper_chunks_staging WHERE version NOT IN (SELECT version FROM (SELECT version FROM medical_paper_chunks_staging ORDER BY version DESC LIMIT 3) AS tmp);"
        paper_queries_and_params.append((paper_fifo_query, ()))

        execute_transaction_query(paper_queries_and_params)
        yield 7