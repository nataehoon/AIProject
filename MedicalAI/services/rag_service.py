from modules.db_repository import execute_select_query
from config import RAG_SIMILARITY

def _get_qa_rag_data(v_data):
        query = f"""
                SELECT question, answer, embedding <=> %s::vector AS distance, 1 - (embedding <=> %s::vector) AS similarity 
                FROM (SELECT B.* FROM prod_version_info A JOIN medical_qa_knowledge_prod B ON A.id = B.version_id WHERE active = True) 
                WHERE (1 - (embedding <=> %s::vector)) >= {RAG_SIMILARITY} 
                ORDER BY distance 
                LIMIT 3;
                """
        params = (v_data, v_data, v_data)
            
        qa_row = execute_select_query(query, params)

        result_rag_text = ""
        for row in qa_row:
            result_rag_text += f"Medical Question: {row['question']}\nExpert Answer: {row['answer']}\nSimilarity: {row['similarity']}\n\n"

        return result_rag_text

def _get_paper_rag_data(v_data):
    query = f"""
            SELECT document_name, page_number, chunk_content, embedding <=> %s::vector AS distance, 1 - (embedding <=> %s::vector) AS similarity 
            FROM (SELECT B.* FROM prod_version_info A JOIN medical_paper_chunks_prod B ON A.id = B.version_id WHERE active = True) 
            WHERE (1 - (embedding <=> %s::vector)) >= {RAG_SIMILARITY} 
            ORDER BY distance 
            LIMIT 3;"""
    params = (v_data, v_data, v_data)

    paper_row = execute_select_query(query, params)

    result_rag_text = ""
    for row in paper_row:
        result_rag_text += f"Paper Name: {row['document_name']}\nAbstract: {row['chunk_content']}\nPage Number: {row['page_number']}\nSimilarity: {row['similarity']}\n\n"

    return result_rag_text

class RAGService:
    @staticmethod
    def get_rag_data(v_data, sources: list[str]):
        rag_text = ""

        for source in sources:
            if source == "qa":
                qa_rag = _get_qa_rag_data(v_data)
                if qa_rag:   
                    rag_text += f"[Q&A]\n{qa_rag}"
            elif source == "paper":
                paper_rag = _get_paper_rag_data(v_data)
                if paper_rag:
                    rag_text += f"[Paper]\n{paper_rag}"
    
        if rag_text:
            rag_text = """
                    You are a medical AI assistant.
    
                    Answer the user's question using the retrieved context as the primary source of information.
    
                    If the retrieved context is insufficient, explicitly state that the available information is insufficient instead of making up facts.\n\n
                    """.strip() + rag_text

        return rag_text