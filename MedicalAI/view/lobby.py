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

raw_data_list = MedicalService.get_raw_data()
qa_list, paper_list = raw_data_list
version = [qa for qa in dict.fromkeys(qa.version for qa in qa_list)]

@st.dialog("수집 데이터", width="large")
def raw_data_info():
    if "selected_version" not in st.session_state:
        st.session_state.selected_version = ""
    with st.container(width=1200, height=650):
        col1, col2 = st.columns([1,5])
        details = []
        with col1:
            st.title("QA")
            for qa in version:
                if st.button(f"{qa}"):
                    st.session_state.selected_version = qa
                    details = []
                    curr_list = [x for x in qa_list if x.version == qa]
                    for content in curr_list:
                        details.append("".join(f"질문: {content.question}\n답변: {content.answer}"))

            st.title("Paper")
            for index, paper in enumerate(version):
                if st.button(f"{paper}", key=f"{index}"):
                    st.session_state.selected_version = paper
                    details = []
                    curr_list = [x for x in paper_list if x.version == paper]
                    for content in set(x.document_name for x in curr_list):
                        details.append("".join(f" - {content}"))
        with col2:
            with st.container(width=1100, height=560):
                if details:
                    for detail in details:
                        st.text(f"{detail}")
                else:
                    st.text("버전을 클릭하시면 저장 내용이 표시됩니다.")
        if details or st.session_state.selected_version:
            btn_col1, btn_col2 = st.columns([16,1])
            with btn_col2:
                if st.button("저장"):
                    MedicalService.save_version_select(st.session_state.selected_version)
                    st.session_state.selected_version = ""

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
            version_list = MedicalService.get_version_info()
            if not version_list == None:
                active_version = next((x for x in version_list if x.active), None)
                no_active_version = [x for x in version_list if x.active == False]
                st.markdown("#### ◆ 버전 정보")
                item_col1, item_col2 = st.columns(2)
                with item_col1:
                    st.markdown("##### Q&A")
                    lit_col1, lit_col2 = st.columns([2,3])
                    with lit_col1:
                        st.text("적용중: ")
                        st.text("전체: ")
                    with lit_col2:
                        st.text(f"{active_version.version}")
                        for no_active in no_active_version:
                            st.text(f"{no_active.version}")
                with item_col2:
                    st.markdown("##### Paper")
                    version_col1, version_col2 = st.columns([2,3])
                    with version_col1:
                        st.text("적용중: ")
                        st.text("전체: ")
                    with version_col2:
                        st.text(f"{active_version.version}")
                        for no_active in no_active_version:
                            st.text(f"{no_active.version}")
            st.markdown("---")

            btn_col1, btn_col2 = st.columns([9,1])
            with btn_col1:
                search = st.button("🔍 데이터 동기화", disabled=st.session_state.searching)
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

            with btn_col2:
                if st.button("ℹ️", key="raw_data_info", disabled=st.session_state.searching):
                    raw_data_info()

            st.markdown("##### 동기화 데이터")
            data_col1, data_col2, data_col3 = st.columns(3)
            with data_col1:
                if len(version) > 0 and version[0]:
                    st.markdown(f"* {version[0]}")
            with data_col2:
                if len(version) > 1 and version[1]:
                    st.markdown(f"* {version[1]}")
            with data_col3:
                if len(version) > 2 and version[2]:
                    st.markdown(f"* {version[2]}")