import streamlit as st
from models.member import UserSessionDTO
from modules.dicomdir_processor import process_dicom_zip
from modules.ai_processor import run_vlm_inference_generator

if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

st.set_page_config(
    page_title="MRI Parsing Engine",
    page_icon="📊",
    layout="wide"
)

st.title(f"{st.session_state.user_profile.name}님 안녕하세요 \n 본 플랫폼은 환자의 병원 정보 데이터를 컨셉에 맞게 가공 후, VLM과 실시간 스트리밍 소켓을 맺어 전문의 수준의 한국어 정밀 소견서 초안을 빌드하는 AX 솔루션 입니다.")

col1, col2 = st.columns([1, 2])
box_height = 650

# 1번째 박스 (첫 번째 열)
with col1:
    with st.container(height=box_height, border=True):
        upload_header_container = st.empty()

        with upload_header_container:
            uploaded_file = st.file_uploader(
                                        label="DICOM (.zip) 파일을 업로드 하세요.",
                                        type=["zip"],
                                        accept_multiple_files=False
                                    )

        if st.session_state.is_processing:
            upload_header_container.empty()
            
        if uploaded_file is not None and not st.session_state.is_processing:
            st.session_state.is_processing=True
            st.rerun()

        if uploaded_file is not None:
            with st.spinner("DICOM 파일을 읽고 있습니다..."):
                dicom_result = process_dicom_zip(uploaded_file)

                if dicom_result["success"]:
                    item_col1, item_col2, item_col3 = st.columns(3)

                    with item_col1:
                        st.text_input("환자 성명", value=dicom_result["patient_name"])
                    with item_col2:
                        st.text_input("환자 ID", value=dicom_result["patient_id"])
                    with item_col3:
                        st.text_input("검사 일자", value=dicom_result["study_date"])
                else:
                    st.error(f"실패하였습니다. {dicom_result['error']}")

            with st.container(height=box_height-120):
                output_placeholder = st.empty()
                
                with output_placeholder.spinner("제공된 정보를 분석하고 있습니다..."):
                    try:
                        vlm_stream = run_vlm_inference_generator(dicom_result)

                        output_placeholder.empty()
                        final_report = ""

                        for text_chunk in vlm_stream:
                            final_report += text_chunk
                            output_placeholder.markdown(final_report + "▌")

                        if final_report:
                            # 최종 확정본 렌더링 (우측의 깜빡이는 커서 ▌ 제거 완료 버전)
                            output_placeholder.markdown(final_report)

                        else:
                            st.error("백엔드 커널로부터 전달받은 텍스트 청크가 유실되어 분석에 실패했습니다.")
                    except Exception as e:
                        output_placeholder.empty()
                        st.error("파일 읽기를 실패하였습니다.")
        else:
            st.info("💡 위의 업로드 박스에 의료 영상 파일을 드롭하면 환자 정보가 자동으로 활성화됩니다.")
            st.info("💡 이미 등록된 파일과 같은 이름은 최신 버전으로 수정됩니다.")


chat_box_height = 60

with col2:
    with st.container(height=box_height ,border=True):
        with st.container(height=box_height-chat_box_height - 90, border=True):
            pass

        st.chat_input(placeholder="내용을 입력하세요.", height=chat_box_height, disabled=st.session_state.is_processing)
