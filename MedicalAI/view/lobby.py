import streamlit as st
import time
from services.medical_service import MedicalService
#from models.member import UserSessionDTO

st.set_page_config(
    page_title="MRI Parsing Engine",
    page_icon="📊",
    layout="wide"
)

if "status" not in st.session_state:
    st.session_state.status = 0

if "searching" not in st.session_state:
    st.session_state.searching = False

status_text = [
    "1. 허깅 페이스에서 Q&A 데이터 받아오는 중...",
    "2. 임베딩 모델 로드 후 백터화 중...",
    "3. 벡터 데이터베이스 저장 및 인덱싱 중...",
    "4. 허깅 페이스에서 논문 데이터를 받아오는 중...",
    "5. 텍스트 청킹 및 전처리 중...",
    "6. 벡터 데이터베이스 저장 및 인덱싱 중...",
    "7. RAG시스템 준비 완료!"
]

one_row_height=500

col1, col2 = st.columns(2)
with col2:
    status_zone = st.empty()

def rerander_status():
    with status_zone:
        with st.container():
            st.header("Status")
            with st.container(height=one_row_height, border=True):
                for index, text in enumerate(status_text):
                    if st.session_state.status -1 == index:
                        st.markdown(f":green[**{text}**]")
                    else:
                        st.markdown(f"{text}")

rerander_status()

with col1:
    st.header("Searched HuggingFace Data")
    paper_placeholder = st.empty()
    with paper_placeholder:
        with st.container(height=one_row_height, border=True):
            search = st.button("🔍 새 자료 찾기", disabled=st.session_state.searching)
            if search or st.session_state.searching == True:
                if st.session_state.searching == False:
                    st.session_state.searching = True
                    st.rerun()
                st.session_state.status = 0
                pipeline = MedicalService.run_rag_pipeline()
                for next_status in pipeline:
                    st.session_state.status = next_status
                    rerander_status()

                st.session_state.searching = False
                st.rerun()