import streamlit as st
import extra_streamlit_components as stx
from services.member_service import MemberService

st.markdown(
    """
    <style>
    /* 사이드바 내부에 표시되는 모든 페이지 링크의 텍스트 크기와 자간 조정 */
    [data-testid="stSidebarNavItems"] span {
        font-size: 16px !important;  /* 기본 폰트 크기를 18px로 시각적 확장 */
        font-weight: 500 !important; /* 폰`트 두께를 약간 두껍게 설정 */
        color: #31333F;             /* 텍스트 색상 지정 */
    }
    </style>
    """,
    unsafe_allow_html=True,  # HTML 및 내부 CSS 스타일 시트 렌더링 허용
)
if "cookie" not in st.session_state:
    st.session_state.cookie = stx.CookieManager()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

cookies = st.session_state.cookie.get_all()

login_page = st.Page("view/login.py", title="로그인", icon="🔒", default=True)
chat_page = st.Page("view/chat.py", title="채팅", icon="💬", default=True) #🤖🧑‍⚕️
lobby_page = st.Page("view/lobby.py", title="대시보드", icon="🧬")
file_research_page = st.Page("view/MRI_Parsing.py", title="파일 분석", icon="🔍")

if "access_token" in cookies:
    token = cookies["access_token"]

    st.session_state.user_profile = MemberService.login_by_token(token)
    pages = [lobby_page, file_research_page, chat_page]
    pg = st.navigation(pages).run()

elif st.session_state.logged_in:
    pages = [lobby_page, file_research_page, chat_page]
    pg = st.navigation(pages).run()
else:
    pg = st.navigation([login_page]).run()