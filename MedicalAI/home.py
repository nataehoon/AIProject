import streamlit as st
import extra_streamlit_components as stx
import time
from services.member_service import MemberService

if "cookie" not in st.session_state:
    st.session_state.cookie = stx.CookieManager()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

cookies = st.session_state.cookie.get_all()

login_page = st.Page("view/login.py", title="로그인", icon="🔒", default=True)
lobby_page = st.Page("view/lobby.py", title="로비", icon="🧬", default=True)

if "access_token" in cookies:
    token = cookies["access_token"]

    st.session_state.user_profile = MemberService.login_by_token(token)
    pg = st.navigation([lobby_page]).run()
elif st.session_state.logged_in:
    pg = st.navigation([lobby_page]).run()
else:
    pg = st.navigation([login_page]).run()