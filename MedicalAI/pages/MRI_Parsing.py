import streamlit as st
from modules.dicomdir_processor import process_dicom_zip
from modules.ai_processor import run_vlm_inference_generator

st.set_page_config(
    page_title="MRI Parsing Engine",
    page_icon="📊",
    layout="wide"
)

st.header("VLM 멀티 프레임 하이브리드 판독 엔진")
st.markdown("---")

uploaded_file = st.file_uploader(
    label="DICOM (.dcm) 파일을 업로드 하세요.",
    type=["zip"],
    accept_multiple_files=False
)

if uploaded_file is not None:
    with st.spinner("DICOM 파일을 읽고 있습니다..."):
        dicom_result = process_dicom_zip(uploaded_file)

    if dicom_result["success"]:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.text_input("환자 성명", value=dicom_result["patient_name"])
        with col2:
            st.text_input("환자 ID", value=dicom_result["patient_id"])
        with col3:
            st.text_input("검사 일자", value=dicom_result["study_date"])

        with st.container(height=600):
            output_placeholder = st.empty()
            
            with output_placeholder.spinner("제공된 정보를 분석하고 있습니다..."):
                try:
                    vlm_stream = run_vlm_inference_generator(dicom_result)

                    if not vlm_stream:
                        output_placeholder.empty()
                        final_report = ""

                        for text_chunk in vlm_stream:
                            final_report += text_chunk
                            output_placeholder.markdown(final_report + "▌")

                        if final_report:
                            # 최종 확정본 렌더링 (우측의 깜빡이는 커서 ▌ 제거 완료 버전)
                            output_placeholder.markdown(final_report)
                            st.success("성공적으로 마쳤습니다.")
                        else:
                            st.error("백엔드 커널로부터 전달받은 텍스트 청크가 유실되어 분석에 실패했습니다.")
                except Exception as e:
                    output_placeholder.empty()
                    st.error("파일 읽기를 실패하였습니다.")
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