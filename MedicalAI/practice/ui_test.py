import streamlit as st
import streamlit.components.v1 as components  # 완전 격리형 컴포넌트 모듈

# -----------------------------------------------------------------------------
# 1. 클릭 이벤트 핸들러 (C#의 SelectionChanged 핸들러 역할)
# -----------------------------------------------------------------------------
# 샌드박스 내부에서 보낸 클릭 신호(URL 쿼리 파라미터)가 들어왔는지 백엔드에서 감지
current_params = st.query_params

# 대화상자(모달) 정의
@st.dialog("변경 확인")
def confirm_change_dialog(selected_value):
    st.write(f"⚠️ 메인 저장값을 **'{selected_value}'**(으)로 변경하시겠습니까?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("예", use_container_width=True, key="modal_yes_action"):
            st.success(f"'{selected_value}'로 메인 저장값 변경 완료!")
            st.query_params.clear()  # 처리 완료 후 URL 쿼리 스트링 청소
            st.rerun()               # 메인 화면 리프레시
    with col2:
        if st.button("아니오", use_container_width=True, key="modal_no_action"):
            st.query_params.clear()
            st.rerun()

# 샌드박스 버튼이 클릭되어 URL 파라미터가 바뀌면 모달창을 띄움
if "target_item" in current_params:
    clicked_data = current_params["target_item"]
    confirm_change_dialog(clicked_data)


# -----------------------------------------------------------------------------
# 2. 메인 UI 및 격리형 가상 버블 리스트 배치
# -----------------------------------------------------------------------------
st.title("메인 데이터 관리 시스템")
st.write("### 변경할 데이터를 선택하세요")

# 독립된 가상 DOM(iframe) 내부에서 HTML/CSS 버튼 3개를 빌드합니다.
# target="_parent" 속성을 주면, iframe 내부가 아닌 메인 크롬 브라우저 창의 URL을 안전하게 변환시킵니다.
isolated_html_component = """
<style>
    /* 이 스타일 시트는 샌드박스 내부에 완전히 갇혀있으므로 외부 버튼을 절대 오염시키지 못합니다. */
    .bubble-btn {
        background-color: #F8F9FA;
        color: #212529;
        border: 1px solid #DEE2E6;
        padding: 12px 20px;
        border-radius: 12px;
        width: 100%;
        text-align: left;
        font-size: 16px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        display: block;
        box-sizing: border-box;
        font-family: sans-serif;
    }
    .bubble-btn:hover {
        background-color: #E8F0FE;
        border-color: #1A73E8;
        color: #1A73E8;
        transform: translateY(-1px);
    }
</style>

<a href="/?target_item=Medical_A" target="_parent" style="text-decoration: none;"><button class="bubble-btn">● 의료 영상 데이터 A</button></a>
<a href="/?target_item=Medical_B" target="_parent" style="text-decoration: none;"><button class="bubble-btn">● 환자 생체 신호 B</button></a>
<a href="/?target_item=Medical_C" target="_parent" style="text-parent; text-decoration: none;"><button class="bubble-btn">● 처방전 로그 데이터 C</button></a>
"""

# 가상 컴포넌트 실행 (정확히 버튼 3개 분량의 높이 155px 확보)
components.html(isolated_html_component, height=200)


st.write("---")

# -----------------------------------------------------------------------------
# 3. 순정 일반 버튼 배치 (100% 무결성 유지)
# -----------------------------------------------------------------------------
# 위 가상 영역 내부의 CSS가 밖으로 탈출할 경로가 원천 차단되었기 때문에,
# 이 버튼은 해상도나 환경에 상관없이 무조건 Streamlit 고유의 순정 회색 정렬 상태를 유지합니다.
st.button("이것은 영향을 받지 않는 시스템 전역 일반 버튼", key="btn_pure_global", use_container_width=True)