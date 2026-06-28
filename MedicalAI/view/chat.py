import streamlit as st
from modules import ai_processor
from services.medical_service import MedicalService
from models.mediinfo import Mediinfo

st.set_page_config(
    page_title="Chatting",
    page_icon="💬",
    layout="wide"
)
 
if "global_chat_history" not in st.session_state:
    st.session_state.global_chat_history = []
    my_medi = MedicalService.get_my_mediinfo(1)
    print(my_medi.model_dump())
    st.session_state.global_chat_history.append({
        "role": "system",
        "content": f"당신은 의료 전공의 수준의 지식을 갖고있는 상담사 입니다. 질문자에게 최대한 이해하기 쉽게 자세하게 설명해 주세요 \n{my_medi.analyzed_text}"
    })

    st.session_state.global_chat_history.append({
        "role": "assistant",
        "content": f"안녕하세요, {st.session_state.user_profile.name}님 어떤 의료 데이터를 함께 검토해 드릴까요?"
    })

if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

st.title("MedicalAI 전문의 메디컬 어시스턴트")
st.caption("본 공간은 임상 쿼리, 논문 레퍼런스 및 환자 차트 데이터 분석을 지원하는 전용 AI 인터페이스 입니다.")
st.divider()

chat_viewport = st.container(height=550, border=False)

with chat_viewport:
    for message in st.session_state.global_chat_history:
        if message["role"] == "user":
            empty_col, content_col, avatar_col = st.columns([2, 7.5, 0.5])
            with content_col:
                st.markdown(f"<p style='text-align: right; margin: 0; margin-top:4px; font-size: 16px; color: #31333F;'>{message['content']}</p>", unsafe_allow_html=True)
                
            with avatar_col: 
                st.markdown("""<div data-testid="stChatMessageAvatarUser" class="st-emotion-cache-23r7bk exttvjz3" 
                                    style="display: flex; justify-content: center; align-items: center; width: 32px; height: 32px; background-color: rgb(255, 75, 75); border-radius: 8px;"">
                                    <span class="st-emotion-cache-leahp2 ewh6kot2">
                                        <span color="inherit" data-testid="stIconMaterial" translate="no" class="st-emotion-cache-1c9yjad ed4y4ls0"
                                            style="display: inline-flex; -webkit-box-align: center; align-items: center; -webkit-box-pack: center; justify-content: center; color: rgb(255 255 255);
                                            font-size: 1.25rem; width: 1.25rem; height: 1.25rem; user-select: none; font-family: "Material Symbols Rounded"; font-weight: 400;
                                            font-style: normal; line-height: 1; letter-spacing: normal; text-transform: none; white-space: nowrap; overflow-wrap: normal; direction: ltr; -webkit-font-smoothing: antialiased;">face</span>
                                    </span>
                                </div>""", unsafe_allow_html=True)
        elif message["role"] == "assistant":
            ai_col, empty_col = st.columns([8,2])
            with ai_col:
                with st.chat_message("assistant"):
                    st.write(message["content"])

if user_query := st.chat_input("의료 질문을 입력하세요.", disabled=st.session_state.is_processing):
    st.session_state.global_chat_history.append({"role": "user", "content": user_query})
    with chat_viewport:
        empty_col, content_col, avatar_col = st.columns([2, 7.5, 0.5])
        with content_col:
            st.markdown(f"<p style='text-align: right; margin: 0; margin-top:4px; font-size: 16px; color: #31333F;'>{user_query}</p>", unsafe_allow_html=True)
            
        with avatar_col: 
            st.markdown("""<div data-testid="stChatMessageAvatarUser" class="st-emotion-cache-23r7bk exttvjz3" 
                                style="display: flex; justify-content: center; align-items: center; width: 32px; height: 32px; background-color: rgb(255, 75, 75); border-radius: 8px;"">
                                <span class="st-emotion-cache-leahp2 ewh6kot2">
                                    <span color="inherit" data-testid="stIconMaterial" translate="no" class="st-emotion-cache-1c9yjad ed4y4ls0"
                                        style="display: inline-flex; -webkit-box-align: center; align-items: center; -webkit-box-pack: center; justify-content: center; color: rgb(255 255 255);
                                        font-size: 1.25rem; width: 1.25rem; height: 1.25rem; user-select: none; font-family: "Material Symbols Rounded"; font-weight: 400;
                                        font-style: normal; line-height: 1; letter-spacing: normal; text-transform: none; white-space: nowrap; overflow-wrap: normal; direction: ltr; -webkit-font-smoothing: antialiased;">face</span>
                                </span>
                            </div>""", unsafe_allow_html=True)

    st.session_state.is_processing=True

    with chat_viewport:
        with st.chat_message("assistant"):
            response_placeholder = st.empty()

            with response_placeholder.spinner("AI의 답변을 기다리는 중입니다."):
                ai_response = ai_processor.run_llm_generator(st.session_state.global_chat_history)

                response_placeholder.empty()
                final_report = ""
                for text_chunk in ai_response:
                    final_report += text_chunk
                    response_placeholder.markdown(final_report + "▌")

                    if final_report:
                        # 최종 확정본 렌더링 (우측의 깜빡이는 커서 ▌ 제거 완료 버전)
                        response_placeholder.markdown(final_report)

    st.session_state.global_chat_history.append({"role": "assistant", "content": final_report})
    st.session_state.is_processing = False
    st.rerun()