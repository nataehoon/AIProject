from modules.db_repository import execute_select_query

sql = "SELECT paragraph_text FROM chunked_paper_vectors WHERE id = %s"
test = execute_select_query(sql, (257,))

print(test)

