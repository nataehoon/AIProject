from modules.db_repository import execute_select_query, execute_non_query, execute_transaction_query

class ChatService:

    @staticmethod
    def send_rout(chatMessage: List[Dict[str, str]], user_id: str):
        query = "SELECT DISTINCT body_part FROM mediinfo WHERE member_id=%s"
        params=(user_id,)

        raw_rows = execute_select_query(query, params)

        my_medi_part = ", ".join(row[0] for row in raw_rows if row[0])

        system_prompt = f""

        chatMessage.append({"role": "user", "content": system_prompt})

        llm_payload = OllamaPayload(
                            model=LLM_MODEL,
                            messages=chatMessage,
                            temperature=DEFAULT_TEMPERATURE,
                            think=LLM_THINK,
                            stream=True,
                            options={"num_predict": LLM_NUM_PREDICT, "num_ctx": LLM_NUM_CTX}
                        ).model_dump()


    @staticmethod
    def send_prompt_llm(chatMessage: List[Dict[str, str]], user_id: str):
        pass

    