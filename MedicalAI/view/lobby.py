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
                    st.markdown("1번 진행중")
                    st.markdown("2번 진행중")
                    st.markdown("3번 진행중")
                if st.session_state.status == 1:
                    st.markdown(":red[1번 진행중]")
                    st.markdown("2번 진행중")
                    st.markdown("3번 진행중")
                if st.session_state.status == 2:
                    st.markdown("1번 진행중")
                    st.markdown(":red[2번 진행중]")
                    st.markdown("3번 진행중")
                if st.session_state.status == 3:
                    st.markdown("1번 진행중")
                    st.markdown("2번 진행중")
                    st.markdown(":red[3번 진행중]")
                if st.session_state.status == 4:
                    st.markdown("1번 진행중")
                    st.markdown("2번 진행중")
                    st.markdown("3번 진행중")
                    st.markdown(":green[완료]")

rerander_status()

with col1:
    st.header("Searched Paper")
    paper_placeholder = st.empty()
    with paper_placeholder:
        with st.container(height=one_row_height, border=True):
            search = st.button("🔍 새 자료 찾기")
            if search:
                st.session_state.status = 0
                st.session_state.status += 1
                rerander_status()
                time.sleep(5)

                st.session_state.status += 1
                rerander_status()
                time.sleep(5)

                st.session_state.status += 1
                rerander_status()
                time.sleep(5)

                st.session_state.status += 1
                rerander_status()
