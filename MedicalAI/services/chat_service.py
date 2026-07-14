from modules.db_repository import execute_select_query, execute_non_query, execute_transaction_query
from typing import List, Dict
import modules.ai_processor as ai_processor
import json

def _pre_data_collection(body_part: List[str], user_id: str):
    query = "SELECT * FROM mediinfo WHERE member_id=%s"
    params=(user_id,)

    raw_rows = execute_select_query(query, params)

    if len(raw_rows) > 0:
        system_prompt = ""
        for row in raw_rows:
            part = row.get("body_part")
            print(f"part: {part}")
            if part in body_part:
                system_prompt += f"분석 부위: {part}\n\n분석 내용: {row.get("analyzed_text", "")}\n\n"

        return system_prompt

def _before_chat_summary(recent_chatMessage: List[Dict[str, str]], summary_chatMessage: str):
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

def _get_rag_data(recent_chatMessage: List[Dict[str, str]], summary_chatMessage: str, sources: List[str]):
    pass

class ChatService:

    @staticmethod
    def run_rout(recent_chatMessage: List[Dict[str, str]], summary_chatMessage: str):
        routMessage = []
        rout_system_prompt = """당신은 의료 AI 시스템의 요청 라우터입니다.

                                현재 사용자 질문을 중심으로 판단하고,
                                최근 대화와 이전 대화 요약은 질문이 모호할 때만 참고하세요.

                                다음 항목을 분류하세요.

                                1. context_relation
                                - continuation: 이전 대화와 직접 연결된 질문 또는 답변
                                - new_topic: 이전 대화와 무관한 새로운 주제

                                2. retrieval_required
                                - true: 의료 관련 질문이며, 정확한 답변을 위해 외부 데이터 검색이 필요함
                                - false: 주어진 문맥과 일반적인 대화 능력만으로 처리 가능함

                                3. sources
                                - qa: 명확하고 직접적인 사실, 정의, 기준, 짧은 답변
                                - paper: 연구 근거 비교, 복합 원인 분석, 깊은 추론
                                - qa와 paper가 모두 필요하면 둘 다 선택
                                - 검색이 필요하지 않으면 빈 배열

                                4. reasoning_level
                                - low
                                - medium
                                - high

                                5. body_part
                                - SHOULDER: 어깨 질문
                                - KNEE: 무릎 질문
                                - HIP: 힙 관절 질문
                                - ANKLE: 발목 질문
                                - WRIST: 손목 질문
                                - ELBOW: 팔꿈치 질문
                                - 복합 질문일 경우 중복 선택 가능함
                                - 특정 관절 질문이 아닌경우 빈 배열

                                6. route는 아래 중 하나로 결정하세요.
                                - DIRECT_CONTINUATION
                                - DIRECT_NEW_TOPIC
                                - RAG_QA
                                - RAG_PAPER
                                - RAG_HYBRID

                                현재 사용자 질문을 과거 대화보다 우선하세요.
                                반드시 JSON만 출력하세요.
                                """.strip()
        routMessage.append({"role": "system", "content": rout_system_prompt})

        recent_assistant = ""
        recent_user = ""
        for prompt in recent_chatMessage:
            if prompt.get("role") == "assistant":
                recent_assistant = prompt.get("content")
            else:
                recent_user = prompt.get("content")

        rout_user_prompt = f"""
                            [이전 대화 정리]
                            {summary_chatMessage}

                            [최신 대화]
                            assistant: {recent_assistant}
                            user: {recent_user}

                            """.strip()

        routMessage.append({"role": "user", "content": rout_user_prompt})

        rout_response = ai_processor.run_router_llm(routMessage)
        result_rout = ""

        for chunk in rout_response:
            result_rout += chunk

        return result_rout

    @staticmethod
    def send_chat(recent_chatMessage: List[Dict[str, str]], summary_chatMessage: str, user_id: str):
        chatMessage = []
        yield {"status": "질문의 의도를 파악하고 있습니다..."}
        rout_result = ChatService.run_rout(recent_chatMessage, summary_chatMessage)
        rout_data = json.loads(rout_result)

        print(f"{rout_data.get("context_relation")} || {rout_data.get("retrieval_required")} || {rout_data.get("body_part")} || {rout_data.get("reasoning_level")} || {rout_data.get("sources")} || {rout_data.get("route")}")

        retrieval = rout_data.get("retrieval_required")

        if retrieval:
            yield {"status": "질문 의도에 맞는 데이터를 불러오고 있습니다..."}

            body_part = rout_data.get("body_part")
            if len(body_part) > 0:
                system_prompt = _pre_data_collection(body_part, user_id)

                if system_prompt:
                    chatMessage.append({"role": "system", "content": system_prompt})

            yield {"status": "질문에 대한 참고 문헌을 조회합니다..."}

            sources = rout_data.get("sources")
            if len(sources) > 0:
                _get_rag_data(recent_chatMessage, summary_chatMessage, sources)


        if len(recent_chatMessage) >= 2:
            yield {"status": "사전 답변을 정리하여 문맥을 파악합니다..."}

            summary_text = _before_chat_summary(recent_chatMessage, summary_chatMessage)
            if summary_text:
                yield {"summary": summary_text}
                chatMessage.append({"role": "system", "content": f"다음은 이전 대화의 요약입니다.\n답변에서는 이 요약을 언급하지 말고 맥락으로만 활용하세요.\n\n{summary_text}"})
    

        yield {"status": "질문을 LLM에게 전달합니다..."}
        for recent_msg in recent_chatMessage:
            chatMessage.append(recent_msg)

        llm_response = ai_processor.run_llm_generator(chatMessage)

        yield {"status": "답변을 불러오는 중입니다..."}
        for chunk in llm_response:
            yield chunk
        



    