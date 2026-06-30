import streamlit as st
import time
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
    "1. 허깅 페이스에서 자료 다운로드 중...",
    "2. 텍스트 청킹 및 전처리 중...",
    "3. 임베딩 모델 로드 후 백터화 중...",
    "4. 벡터 데이터베이스 저장 및 인덱싱 중...",
    "5. RAG시스템 준비 완료!"
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
                if st.session_state.status == 0:
                    st.markdown(f"{status_text[0]}")
                    st.markdown(f"{status_text[1]}")
                    st.markdown(f"{status_text[2]}")
                    st.markdown(f"{status_text[3]}")
                    st.markdown(f"{status_text[4]}")
                if st.session_state.status == 1:
                    st.markdown(f":green[{status_text[0]}]")
                    st.markdown(f"{status_text[1]}")
                    st.markdown(f"{status_text[2]}")
                    st.markdown(f"{status_text[3]}")
                    st.markdown(f"{status_text[4]}")
                if st.session_state.status == 2:
                    st.markdown(f"{status_text[0]}")
                    st.markdown(f":green[{status_text[1]}]")
                    st.markdown(f"{status_text[2]}")
                    st.markdown(f"{status_text[3]}")
                    st.markdown(f"{status_text[4]}")
                if st.session_state.status == 3:
                    st.markdown(f"{status_text[0]}")
                    st.markdown(f"{status_text[1]}")
                    st.markdown(f":green[{status_text[2]}]")
                    st.markdown(f"{status_text[3]}")
                    st.markdown(f"{status_text[4]}")
                if st.session_state.status == 4:
                    st.markdown(f"{status_text[0]}")
                    st.markdown(f"{status_text[1]}")
                    st.markdown(f"{status_text[2]}")
                    st.markdown(f":green[{status_text[3]}]")
                    st.markdown(f"{status_text[4]}")
                if st.session_state.status == 5:
                    st.markdown(f"{status_text[0]}")
                    st.markdown(f"{status_text[1]}")
                    st.markdown(f"{status_text[2]}")
                    st.markdown(f"{status_text[3]}")
                    st.markdown(f":green[{status_text[4]}]")

rerander_status()

with col1:
    st.header("Searched Paper")
    paper_placeholder = st.empty()
    with paper_placeholder:
        with st.container(height=one_row_height, border=True):
            search = st.button("🔍 새 자료 찾기", disabled=st.session_state.searching)
            if search or st.session_state.searching == True:
                if st.session_state.searching == False:
                    st.session_state.searching = True
                    st.rerun()
                st.session_state.status = 0
                st.session_state.status += 1
                rerander_status()
                time.sleep(2)

                st.session_state.status += 1
                rerander_status()
                time.sleep(2)

                st.session_state.status += 1
                rerander_status()
                time.sleep(2)

                st.session_state.status += 1
                rerander_status()
                time.sleep(2)

                st.session_state.status += 1
                rerander_status()

                st.session_state.searching = False
                st.rerun()