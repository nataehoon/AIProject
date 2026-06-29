import streamlit as st
from models.member import UserSessionDTO

st.set_page_config(
    page_title="MRI Parsing Engine",
    page_icon="📊",
    layout="wide"
)

one_row_height=500

col1, col2 = st.columns(2)
with col1:
    st.header("Searched Paper")
    paper_placeholder = st.empty()
    with paper_placeholder:
        with st.container(height=one_row_height, border=True):
            st.button("🔍 새 자료 찾기")
with col2:
    st.header("Status")
    status_placeholder = st.empty()
    with status_placeholder:
        with st.container(height=one_row_height, border=True):
            st.markdown(":red[1번 진행중]")
            st.markdown("2번 진행중")
            st.markdown("3번 진행중")
