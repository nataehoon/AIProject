import streamlit as st

st.markdown(
    """
    <style>
    /* 사이드바 내부에 표시되는 모든 페이지 링크의 텍스트 크기와 자간 조정 */
    [data-testid="stSidebarNavItems"] span {
        font-size: 18px !important;  /* 기본 폰트 크기를 18px로 시각적 확장 */
        font-weight: 500 !important; /* 폰트 두께를 약간 두껍게 설정 */
        color: #31333F;             /* 텍스트 색상 지정 */
    }
    </style>
    """,
    unsafe_allow_html=True,  # HTML 및 내부 CSS 스타일 시트 렌더링 허용
)

if not "logged_in" in st.session_state:
    st.session_state.logged_in = False

login_page = st.Page("view/login.py", title="로그인", icon="🔒", default=True)
chat_page = st.Page("view/chat.py", title="채팅", icon="💬", default=True) #🤖🧑‍⚕️
lobby_page = st.Page("view/lobby.py", title="대시보드", icon="🧬")
file_research_page = st.Page("view/MRI_Parsing.py", title="파일 분석", icon="🔍")

if st.session_state.logged_in:
    pages = [lobby_page, file_research_page, chat_page]
else:
    pages = [login_page]

pg = st.navigation(pages)
pg.run()