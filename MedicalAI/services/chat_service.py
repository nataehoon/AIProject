from modules.db_repository import execute_select_query, execute_non_query, execute_transaction_query
from typing import List, Dict
import modules.ai_processor as ai_processor
import json
from modules.sentence_transformer import encode
from services.rag_service import RAGService

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
                system_prompt += f"research_boy_part: {part}\n\nresearch_content: {row.get("analyzed_text", "")}\n\n"

        return system_prompt

def _before_chat_summary(recent_chatMessage: List[Dict[str, str]], summary_chatMessage: str):
    summaryMessage = []
    summary_system_prompt = """
        You are a conversation summarization assistant.

        Your goal is to maintain a concise and up-to-date summary of the conversation so that another AI can naturally continue the dialogue later.

        Instructions:

        - Merge the existing summary and the new conversation into a single updated summary.
        - Preserve all important information from the existing summary unless it has been explicitly corrected or replaced.
        - Incorporate any new or updated information from the latest conversation.
        - Eliminate redundant or duplicate information.
        - Preserve unresolved questions, pending tasks, and topics that still require follow-up.
        - Never remove the user's goals, preferences, or other important facts.
        - Do not infer, assume, or invent information that was not explicitly stated.
        - Keep the summary concise while preserving all essential context.

        Output only the updated summary.
        Do not include explanations, markdown, or any additional text.
        """.strip()
    
    summaryMessage.append({"role": "system", "content": summary_system_prompt})

    recent_assistant = ""
    recent_user = ""
    for prompt in recent_chatMessage:
        if prompt.get("role") == "assistant":
            recent_assistant = prompt.get("content")
        else:
            recent_user = prompt.get("content")

    summary_user_prompt = f"[Existing summary body]\n{summary_chatMessage}\n\n[New conversation]\n\nassistant: {recent_assistant}\nuser: {recent_user}"
    summaryMessage.append({"role": "user", "content": summary_user_prompt})

    summary_response = ai_processor.run_llm_generator(summaryMessage)
    summary_text = ""
    for chunk in summary_response:
        summary_text += chunk

def _get_rag_data(recent_chatMessage: List[Dict[str, str]], summary_chatMessage: str, sources: List[str]):
    ragMessage = []
    rag_system_prompt = """
                        You are a query rewriting engine for a Retrieval-Augmented Generation (RAG) system.

                        Your task is to convert the user's current question and the previous conversation into a single search query.

                        Rules:
                        1. Understand the user's true intent using both the conversation history and the latest user message.
                        2. Resolve omitted subjects, pronouns, and references using the conversation history.
                        3. Extract only the essential concepts required for semantic retrieval.
                        4. Remove greetings, filler words, emotions, and conversational expressions.
                        5. Do not answer the question.
                        6. Do not explain anything.
                        7. Return exactly one concise sentence.
                        8. Preserve important technical terms, library names, model names, database names, APIs, and programming languages.
                        9. If the user asks a follow-up question, rewrite it into a standalone search query.
                        10. The output should be optimized for embedding-based similarity search.

                        Output:
                        One sentence only.
                        """.strip()

    ragMessage.append({"role": "system", "content": rag_system_prompt})

    recent_assistant = ""
    recent_user = ""
    for prompt in recent_chatMessage:
        if prompt.get("role") == "assistant":
            recent_assistant = prompt.get("content")
        else:
            recent_user = prompt.get("content")

    rag_user_prompt = f"[Existing summary body]\n{summary_chatMessage}\n\n[New conversation]\n\nassistant: {recent_assistant}\nuser: {recent_user}"
    ragMessage.append({"role": "user", "content": rag_user_prompt})

    rag_response = ai_processor.run_llm_generator(ragMessage)
    rag_text = ""
    for chunk in rag_response:
        rag_text += chunk

    v_data = encode(rag_text)

    rag_text = ""
    for source in sources:
        if source == "qa":
            qa_rag = RAGService.get_rag_data(v_data)
            if qa_rag:
                rag_text += f"[Q&A]\n{qa_rag}"
        elif source == "paper":
            paper_rag = RAGService.get_rag_data(v_data)
            if paper_rag:
                rag_text += f"[Paper]\n{paper_rag}"

    if rag_text:
        rag_text = """
                System

                You are a medical AI assistant.

                Answer the user's question using the retrieved context as the primary source of information.

                If the retrieved context is insufficient, explicitly state that the available information is insufficient instead of making up facts.

                Always answer in Korean.\n\n
                """.strip() + rag_text

    return rag_text

class ChatService:

    @staticmethod
    def run_rout(recent_chatMessage: List[Dict[str, str]], summary_chatMessage: str):
        routMessage = []
        rout_system_prompt = """You are a request router for a medical AI system.

                                Prioritize the user's latest message when making decisions.
                                Use the recent conversation history and previous conversation summary only if the current question is ambiguous or depends on prior context.

                                Classify the request according to the following fields.

                                1. context_relation
                                - continuation: The user's question is directly related to the previous conversation.
                                - new_topic: The user's question introduces a new topic unrelated to the previous conversation.

                                2. retrieval_required
                                - true: The request is medical-related and requires external knowledge retrieval to provide an accurate answer.
                                - false: The request can be answered using the current conversation context and the model's general knowledge.

                                3. sources
                                Select one or more of the following:
                                - qa: For factual questions, definitions, diagnostic criteria, guidelines, or short direct answers.
                                - paper: For research evidence, literature comparison, complex reasoning, or in-depth medical analysis.
                                - Select both "qa" and "paper" if both are needed.
                                - Return an empty array if retrieval is not required.

                                4. reasoning_level
                                Choose one of:
                                - low
                                - medium
                                - high

                                5. body_part
                                Select one or more of the following if applicable:
                                - SHOULDER
                                - KNEE
                                - HIP
                                - ANKLE
                                - WRIST
                                - ELBOW

                                If the question involves multiple joints, include all relevant body parts.
                                If the question is not about a specific joint, return an empty array.

                                6. route
                                Choose exactly one of the following:
                                - DIRECT_CONTINUATION
                                - DIRECT_NEW_TOPIC
                                - RAG_QA
                                - RAG_PAPER
                                - RAG_HYBRID

                                Decision Guidelines:
                                - Always prioritize the user's latest message over previous conversations.
                                - Use conversation history only when necessary to resolve references or ambiguity.
                                - If retrieval is not required, the route must be either DIRECT_CONTINUATION or DIRECT_NEW_TOPIC.
                                - If retrieval is required:
                                - Use RAG_QA for factual questions.
                                - Use RAG_PAPER for research-oriented or evidence-based questions.
                                - Use RAG_HYBRID when both QA knowledge and research literature are needed.

                                Return only a valid JSON object.
                                Do not include any explanations, markdown, or additional text.
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
                rag_data = _get_rag_data(recent_chatMessage, summary_chatMessage, sources)
                print(f"rag_data: {rag_data}")
                chatMessage.append({"role": "system", "content": f"{rag_data}"})

        if len(recent_chatMessage) >= 2:
            yield {"status": "사전 답변을 정리하여 문맥을 파악합니다..."}

            summary_text = _before_chat_summary(recent_chatMessage, summary_chatMessage)
            if summary_text:
                yield {"summary": summary_text}
                chatMessage.append({"role": "system", "content": f"The following is a summary of the previous conversation.\nPlease use this summary only for context and do not mention it in your response.\n\n{summary_text}"})
    

        yield {"status": "질문을 LLM에게 전달합니다..."}
        for recent_msg in recent_chatMessage:
            chatMessage.append(recent_msg)

        llm_response = ai_processor.run_llm_generator(chatMessage)

        yield {"status": "답변을 불러오는 중입니다..."}
        for chunk in llm_response:
            yield chunk
        



    