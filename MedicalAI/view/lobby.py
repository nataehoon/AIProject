import streamlit as st

st.set_page_config(
    page_title="MRI Parsing Engine",
    page_icon="📊",
    layout="wide"
)

st.title(f"{st.session_state.user_profile["user_id"]}님 안녕하세요 \n 병력 진단 시스템")
st.markdown("---")

st.subheader("시스템 아키텍처 개요")
st.info(
    "본 플랫폼은 환자의 병원 정보 데이터를 컨셉에 맞게 가공 후, VLM과 실시간 스트리밍 소켓을 맺어 전문의 수준의 한국어 정밀 소견서 초안을 빌드하는 AX 솔루션 입니다."
)

col1, col2, col3, col4 = st.columns(4)

# 1번째 박스 (첫 번째 열)
with col1:
    # border=True 옵션을 주어 가로 25% 면적을 가진 사각형 테두리를 형성합니다.
    with st.container(border=True):
        st.markdown("#### 🩻 1번 전경 (CR)")
        st.caption("골격 정렬 상태")
        st.write("정상 배열 상태 유지 중이며, 탈구 및 골절 소견 미발견. 관절 공간 안정적.")

# 2번째 박스 (두 번째 열)
with col2:
    with st.container(border=True):
        st.markdown("#### 🩻 2번 측면 (CR)")
        st.caption("이질적 구조 변화")
        st.write("전체적인 뼈의 연속성 확인됨. 피질골 내 구조적 변형 또는 이탈 소견 없음.")

# 3번째 박스 (세 번째 열)
with col3:
    with st.container(border=True):
        st.markdown("#### 🧬 3번 단면 (MRI)")
        st.caption("디스크 팽윤 여부")
        st.write("L4-5 디스크의 미세한 팽윤이 의심되나, 신경근을 압박하는 채널은 발견되지 않음.")

# 4번째 박스 (네 번째 열)
with col4:
    with st.container(border=True):
        st.markdown("#### 🧬 4번 종단 (MRI)")
        st.caption("최종 요약 결론")
        st.write("중증 협착증 소견 없음. 근육 긴장으로 인한 비특이적 요통 가능성 높음.")