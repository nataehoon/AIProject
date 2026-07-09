from modules.db_repository import execute_select_query

class RAGService:
    def get_rag_data(v_data):
        query = "SELECT question, answer FROM (SELECT B.* FROM prod_version_info A JOIN medical_qa_knowledge_prod B ON A.id = B.version_id WHERE active = True) ORDER BY embedding <=> %s::vector LIMIT 1;"
        params = (v_data,)

        qa_row = execute_select_query(query, params)[0]

        query = "SELECT document_name, page_number, chunk_content FROM (SELECT B.* FROM prod_version_info A JOIN medical_paper_chunks_prod B ON A.id = B.version_id WHERE active = True) ORDER BY embedding <=> %s::vector LIMIT 1;"
        params = (v_data,)

        paper_row = execute_select_query(query, params)[0]

        result_rag_text = f"Medical Question: {qa_row["question"]}\nExpert Answer: {qa_row["answer"]}\nPaper Name: {paper_row["document_name"]}\nAbstract: {paper_row["chunk_content"]}\nPage Number: {paper_row["page_number"]}"
        return result_rag_text