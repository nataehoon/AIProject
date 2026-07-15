import streamlit as st
from services.medical_service import MedicalService
import pandas as pd

st.set_page_config(
    page_title="DICOM Parsing Engine",
    page_icon="📊",
    layout="wide"
)

@st.dialog("알림")
def _already_uploaded_file():
    st.warning("이미 등록된 파일입니다.")
    col1, col2 = st.columns([3,1])
    with col2:
        if st.button("확인"):
            if "dicom_file_uploader" in st.session_state:
                del st.session_state["dicom_file_uploader"]
            st.rerun()

st.title("DICOM 파일 관리")
st.markdown("---")

uploaded_file = st.file_uploader(
    label="DICOM (.zip) 파일을 업로드 하세요.",
    type=["zip"],
    accept_multiple_files=False,
    key="dicom_file_uploader"
)

my_medi_info = MedicalService.get_my_mediinfo(st.session_state.user_profile.id)
if my_medi_info:
    rows=[]
    for row in my_medi_info:
        rows.append({"부위": row.body_part, "방식": row.modality, "파일 이름": row.file_name, "분석 본문": row.analyzed_text})
    df = pd.DataFrame(rows)
    st.dataframe(df)

if uploaded_file is not None:
    if my_medi_info:
        if uploaded_file.name in (row.file_name for row in my_medi_info):
            _already_uploaded_file()

    upload_result = MedicalService.dicom_file_process(uploaded_file, st.session_state.user_profile.id)
    with st.status("🔍 AI 하이브리드 판독 엔진 구동 중...", expanded=False) as status:
        for result in upload_result:
            st.write(result.get("status", "처리 중..."))
