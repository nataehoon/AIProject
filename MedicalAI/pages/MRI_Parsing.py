import streamlit as st
from modules.dicomdir_processor import process_dicom_zip

st.set_page_config(
    page_title="MRI Parsing Engine",
    page_icon="📊",
    layout="wide"
)

st.header("VLM 멀티 프레임 하이브리드 판독 엔진")
st.markdown("---")

has_file = False

uploaded_file = st.file_uploader(
    label="DICOM (.dcm) 파일을 업로드 하세요.",
    type=["zip"],
    accept_multiple_files=False
)

if uploaded_file is not None:
    has_file = True
    with st.spinner("DICOM 파일을 읽고 있습니다..."):
        dicom_result = process_dicom_zip(uploaded_file)

    if dicom_result["success"]:
        col1, col2, col3 = st.columns(3)

        with col1:
            p_name = st.text_input("환자 성명", value=dicom_result["patient_name"])
        with col2:
            p_id = st.text_input("환자 ID", value=dicom_result["patient_id"])
        with col3:
            s_date = st.text_input("검사 일자", value=dicom_result["study_date"])

        st.success("DICOM 메타데이터 자동 매핑 완료.")
    else:
        st.error(f"실패하였습니다. {dicom_result['error']}")
else:
    has_file = True
    col1, col2, col3 = st.columns(3)
    with col1:
        st.text_input("환자 성명", value="", placeholder="파일을 업로드하면 자동 입력됩니다", disabled=True)
    with col2:
        st.text_input("환자 ID", value="", placeholder="파일을 업로드하면 자동 입력됩니다", disabled=True)
    with col3:
        st.text_input("검사 일자", value="", placeholder="파일을 업로드하면 자동 입력됩니다", disabled=True)
    st.info("💡 위의 업로드 박스에 의료 영상 파일을 드롭하면 환자 정보가 자동으로 활성화됩니다.")