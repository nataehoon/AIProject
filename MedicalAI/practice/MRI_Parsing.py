import streamlit as st
from modules.dicomdir_processor import process_dicom_zip
from modules.ai_processor import run_vlm_inference_generator
from models.mediinfo import Mediinfo
from services.medical_service import MedicalService
import pandas as pd

st.set_page_config(
    page_title="MRI Parsing Engine",
    page_icon="📊",
    layout="wide"
)

st.header("VLM 멀티 프레임 하이브리드 판독 엔진")
st.markdown("---")

@st.dialog("알림")
def _already_uploaded_file():
    st.warning("이미 등록된 파일입니다.")
    col1, col2 = st.columns([3,1])
    with col2:
        if st.button("확인"):
            if "dicom_file_uploader" in st.session_state:
                del st.session_state["dicom_file_uploader"]
            st.rerun()

my_medi_info = MedicalService.get_my_mediinfo(st.session_state.user_profile.id)
rows = []
for row in my_medi_info:
    rows.append({"부위": row.body_part, "Modality": row.modality, "파일 이름": row.file_name, "정리 본문": row.analyzed_text})
df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)

uploaded_file = st.file_uploader(
    label="DICOM (.zip) 파일을 업로드 하세요.",
    type=["zip"],
    accept_multiple_files=False,
    key="dicom_file_uploader"
)

if uploaded_file is not None:
    my_medi = Mediinfo()

    if my_medi_info:
        for medi_data in my_medi_info:
            if uploaded_file.name == medi_data.file_name:
                _already_uploaded_file()

        my_medi.member_id = st.session_state.user_profile.id
        my_medi.file_name = uploaded_file.name
        with st.spinner("DICOM 파일을 읽고 있습니다..."):
            dicom_result = process_dicom_zip(uploaded_file)

        if dicom_result["success"]:
            my_medi.modality = ",".join(dicom_result["pixel_buffer"])
            my_medi.body_part = dicom_result["body_part"]

            col1, col2, col3 = st.columns(3)

            with col1:
                st.text_input("환자 성명", value=dicom_result["patient_name"])
            with col2:
                st.text_input("환자 ID", value=dicom_result["patient_id"])
            with col3:
                st.text_input("검사 일자", value=dicom_result["study_date"])

            result_success = False

            vlm_stream = run_vlm_inference_generator(dicom_result)
            
            result_text_container = st.empty()
            with st.status("🔍 AI 하이브리드 판독 엔진 구동 중...", expanded=True) as status:
                result_text_container.empty()
                for result_chunk in vlm_stream:
                    if isinstance(result_chunk, dict):
                        status_text = result_chunk.get("status", "처리 중...")
                        body_part = result_chunk.get("body_part", "")
                        if body_part:
                            my_medi.body_part = body_part
                        st.write(status_text)
                    else:
                        my_medi.analyzed_text = result_chunk
                        print(my_medi.model_dump())
                        save_result = MedicalService.save_my_mediinfo(my_medi=my_medi)
                        if save_result:
                            st.write("성공적으로 분석 내용을 저장 하였습니다.")
                        break
        else:
            st.error(f"실패하였습니다. {dicom_result['error']}")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.text_input("환자 성명", value="", placeholder="파일을 업로드하면 자동 입력됩니다", disabled=True)
    with col2:
        st.text_input("환자 ID", value="", placeholder="파일을 업로드하면 자동 입력됩니다", disabled=True)
    with col3:
        st.text_input("검사 일자", value="", placeholder="파일을 업로드하면 자동 입력됩니다", disabled=True)
    st.info("💡 위의 업로드 박스에 의료 영상 파일을 드롭하면 환자 정보가 자동으로 활성화됩니다.")
