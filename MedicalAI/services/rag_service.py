from modules.db_repository import execute_select_query

class RAGService:
    def get_qa_rag_data(v_data):
        query = """
                SELECT question, answer, embedding <=> %s::vector AS distance, 1 - (embedding <=> %s::vector) AS similarity 
                FROM (SELECT B.* FROM prod_version_info A JOIN medical_qa_knowledge_prod B ON A.id = B.version_id WHERE active = True) 
                WHERE (1 - (embedding <=> %s::vector)) >= 0.75 
                ORDER BY distance 
                LIMIT 3;
                """
        params = (v_data, v_data, v_data)
            
        qa_row = execute_select_query(query, params)

        result_rag_text = ""
        for row in qa_row:
            result_rag_text += f"Medical Question: {row['question']}\nExpert Answer: {row['answer']}\nSimilarity: {row['similarity']}\n\n"

        return result_rag_text

    def get_rag_data(v_data):
        query = """
                SELECT document_name, page_number, chunk_content, embedding <=> %s::vector AS distance, 1 - (embedding <=> %s::vector) AS similarity 
                FROM (SELECT B.* FROM prod_version_info A JOIN medical_paper_chunks_prod B ON A.id = B.version_id WHERE active = True) 
                WHERE (1 - (embedding <=> %s::vector)) >= 0.75 
                ORDER BY distance 
                LIMIT 3;"""
        params = (v_data, v_data, v_data)

        paper_row = execute_select_query(query, params)

        result_rag_text = ""
        for row in paper_row:
            result_rag_text += f"Paper Name: {row['document_name']}\nAbstract: {row['chunk_content']}\nPage Number: {row['page_number']}\nSimilarity: {row['similarity']}\n\n"

        return result_rag_text