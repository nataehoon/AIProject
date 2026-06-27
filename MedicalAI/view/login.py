import streamlit as st
from models.member import Member
from services.member_service import MemberService
import extra_streamlit_components as stx
import time

cookie_manager = stx.CookieManager()

cookie_data = cookie_manager.get("access_token")
if cookie_data:
    st.session_state.logged_in = True
    st.session_state.user_profile = MemberService.login_by_token(cookie_data)
    
    st.rerun()

st.title("MedicalAI 로그인")

def validation(user_id:str, user_pw:str) -> str | None:
    if not user_id or not user_pw:
        return "아이디와 패스워드를 입력해 주세요."
    return None

with st.form(key="login_form"):
    user_id = st.text_input("아이디(ID)", placeholder="아이디를 입력하세요.")
    user_pw = st.text_input("비밀번호(password)", type="password", placeholder="비밀번호를 입력하세요.")

    submit_button = st.form_submit_button(label="로그인")

    st.session_state.user_profile = {}
    if submit_button:
        validation_result = validation(user_id, user_pw)

        if validation_result:
            st.error(validation_result)
        else:
            token = MemberService.login_process(user_id, user_pw)

            if token:
                cookie_manager.set("access_token", token, max_age=3600)
                time.sleep(0.5)
                st.session_state.logged_in = True
                st.session_state.user_profile = MemberService.login_by_token(token)

                st.rerun()
            else:
                st.error("아이디와 패스워드를 다시 확인해 주세요.")

