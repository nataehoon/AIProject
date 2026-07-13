from modules.db_repository import execute_select_query, execute_non_query, execute_transaction_query
from typing import List, Dict
import modules.ai_processor as ai_processor

class ChatService:

    @staticmethod
    def send_rout(recent_chatMessage: List[Dict[str, str]], summary_chatMessage: str, user_id: str):
        chatMessage = []
        yield {"status": "질문의 의도를 파악하고 있습니다..."}


        yield {"status": "질문 의도에 맞는 데이터를 불러오고 있습니다..."}
        query = "SELECT * FROM mediinfo WHERE member_id=%s"
        params=(user_id,)

        raw_rows = execute_select_query(query, params)

        if len(raw_rows) > 0:
            my_medi_part = ", ".join({row.get("body_part") for row in raw_rows if row.get("body_part")})
            print(f"raw_rows: {my_medi_part}")

            system_prompt = f"분석 부위: {my_medi_part}\n\n분석 내용: {raw_rows[0].get("analyzed_text", "")}"

            chatMessage.append({"role": "system", "content": system_prompt})

        if len(recent_chatMessage) >= 2:
            yield {"status": "사전 답변을 정리하여 문맥을 파악합니다..."}
            summaryMessage = []
            summary_system_prompt = """
                당신은 대화 기록을 압축하는 요약기입니다.

                목표는 이후 AI가 자연스럽게 대화를 이어갈 수 있도록
                대화의 핵심 맥락만 유지하는 것입니다.

                규칙

                - 기존 요약과 새로운 대화를 하나의 최신 요약으로 통합합니다.
                - 기존 요약에 있는 중요한 정보는 유지합니다.
                - 새로운 대화에서 추가되거나 변경된 정보를 반영합니다.
                - 같은 내용은 중복해서 작성하지 않습니다.
                - 아직 해결되지 않은 질문이나 확인이 필요한 내용은 반드시 유지합니다.
                - 사용자의 목적과 중요한 사실은 절대 삭제하지 않습니다.
                - 새로운 정보를 만들어내지 않습니다.
                - 요약문만 출력합니다.
                """.strip()
            
            summaryMessage.append({"role": "system", "content": summary_system_prompt})

            recent_assistant = ""
            recent_user = ""
            for prompt in recent_chatMessage:
                if prompt.get("role") == "assistant":
                    recent_assistant = prompt.get("content")
                else:
                    recent_user = prompt.get("content")

            summary_user_prompt = f"[기존 요약 본문]\n{summary_chatMessage}\n\n[새 대화]\n\nassistant: {recent_assistant}\nuser: {recent_user}"
            summaryMessage.append({"role": "user", "content": summary_user_prompt})

            summary_response = ai_processor.run_llm_generator(summaryMessage)
            summary_text = ""
            for chunk in summary_response:
                summary_text += chunk

            yield {"summary": summary_text}
            chatMessage.append({"role": "system", "content": f"다음은 이전 대화의 요약입니다.\n답변에서는 이 요약을 언급하지 말고 맥락으로만 활용하세요.\n\n{summary_text}"})

        for recent_msg in recent_chatMessage:
            chatMessage.append(recent_msg)

        yield {"status": "질문을 LLM에게 전달합니다..."}
        llm_response = ai_processor.run_llm_generator(chatMessage)

        yield {"status": "답변을 불러오는 중입니다..."}
        for chunk in llm_response:
            yield chunk
        



    