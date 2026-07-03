from modules.db_repository import execute_select_query, execute_non_query
from models.mediinfo import Mediinfo
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from datasets import load_dataset
import numpy as np

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
        embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

        qa_dataset = load_dataset("lavita/MedQuAD", split="train[:50]")
        yield 1

        qa_texts = []
        for row in qa_dataset:
            combined = f"Medical Question: {row['question'].strip()}\nExpert Answer: {row['answer'].strip()}"
            qa_texts.append(combined)

        qa_embeddings = embedding_model.encode(qa_texts)
        yield 2

        qa_query = "INSERT INTO medical_qa_knowledge(qeustion, answer, combined_content, specialty, embedding) VALUES(%s, %s, %s, %s, %s);"
        qa_params = []
        for index, row in enumerate(qa_dataset):
            v_data = np.array(qa_embeddings[index], dtype=np.float32).tolist() # ???
            qa_params.append((row['question'], row['answer'], qa_texts[index], "General", v_data))

        for param in qa_params:
            execute_non_query(qa_query, param)
        yield 3

        paper_dataset = load_dataset("ahmedabdelwahed/Medical_papers_title_and_abstract_NLP_dataset", split="train[:20]") # train???
        yield 4

        paper_chunks_data = []
        for paper in paper_dataset:
            title = paper["title"]
            abstract = paper["abstract"] # ???

            chunk_size = 1000
            for start_idx in range(0, len(abstract), chunk_size):
                chunk_str = abstract[start_idx: start_idx + chunk_size]
                paper_chunks_data.append({"title": title, "content": chunk_str})

        chunk_texts = [item["content"] for item in paper_chunks_data]
        paper_embeddings = embedding_model.encode(chunk_texts)
        yield 5

        paper_query = "INSERT INTO medical_paper_chunks(document_name, page_number, chunk_index, chunk_content, embedding) VALUES(%s, %s, %s, %s, %s);"
        for index, item in enumerate(paper_chunks_data):
            v_data = np.array(paper_embeddings[index], dtype=np.float32).tolist()
            execute_non_query(paper_query, (item["title"], 1, index, item["content"]), v_data)
        yield 6