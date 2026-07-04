import streamlit as st
from modules.dicomdir_processor import process_dicom_zip
from modules.ai_processor import run_vlm_inference_generator
from models.mediinfo import Mediinfo
from services.medical_service import MedicalService

st.set_page_config(
    page_title="MRI Parsing Engine",
    page_icon="📊",
    layout="wide"
)

st.header("VLM 멀티 프레임 하이브리드 판독 엔진")
st.markdown("---")

uploaded_file = st.file_uploader(
    label="DICOM (.zip) 파일을 업로드 하세요.",
    type=["zip"],
    accept_multiple_files=False
)

if "retry" not in st.session_state:
    st.session_state.retry = False

my_medi = Mediinfo()
result_text_container = st.empty()
def save_retry():
    re_try = st.button("재시도")
    if re_try:
        save_result = MedicalService.save_my_mediinfo(my_medi=my_medi)
        result_text_container.empty()
        with result_text_container:
            if save_result > 0:
                st.success("성공적으로 분석 내용을 저장 하였습니다.")
            else:
                st.error("분석 저장에 실패하였습니다. 다시 시도하시려면 아래 버튼을 눌러주세요.")
                save_retry()

if uploaded_file is not None and not st.session_state.retry:
    my_medi.member_id = 1
    my_medi.file_name = uploaded_file.name
    with st.spinner("DICOM 파일을 읽고 있습니다..."):
        dicom_result = process_dicom_zip(uploaded_file)

    if dicom_result["success"]:
        my_medi.modality = ",".join(dicom_result["pixel_buffer"])

        col1, col2, col3 = st.columns(3)

        with col1:
            st.text_input("환자 성명", value=dicom_result["patient_name"])
        with col2:
            st.text_input("환자 ID", value=dicom_result["patient_id"])
        with col3:
            st.text_input("검사 일자", value=dicom_result["study_date"])

        result_success = False

        output_placeholder = st.empty()
        
        with output_placeholder.spinner("🧐 제공된 정보를 분석하고 있습니다..."):
            try:
                vlm_stream = run_vlm_inference_generator(dicom_result)

                output_placeholder.empty()
                final_report = ""

                for text_chunk in vlm_stream:
                    final_report += text_chunk
                    output_placeholder.markdown(final_report + "▌")

                if final_report:
                    output_placeholder.markdown(final_report)
                    result_success = True
                else:
                    st.error("백엔드 커널로부터 전달받은 텍스트 청크가 유실되어 분석에 실패했습니다.")
            except Exception as e:
                output_placeholder.empty()
                st.error("파일 읽기를 실패하였습니다.")
        if result_success:
            my_medi.analyzed_text = final_report
            print(my_medi.model_dump())
            save_result = MedicalService.save_my_mediinfo(my_medi=my_medi)
            result_text_container.empty()
            with result_text_container:
                if save_result:
                    st.success("성공적으로 분석 내용을 저장 하였습니다.")
                else:
                    st.error("분석 저장에 실패하였습니다. 다시 시도하시려면 아래 버튼을 눌러주세요.")
                    st.session_state.retry = True
                    save_retry()
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
