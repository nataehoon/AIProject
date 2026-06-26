import streamlit as st

st.title("MedicalAI 로그인")
    
with st.form(key="login_form"):
    user_id = st.text_input("아이디(ID)", placeholder="아이디를 입력하세요.")
    user_pw = st.text_input("비밀번호(password)", type="password", placeholder="비밀번호를 입력하세요.")

    submit_button = st.form_submit_button(label="로그인")

    st.session_state.user_profile = {}
    if submit_button:
        st.session_state.logged_in = True
        st.session_state.user_profile = {
            "user_id": user_id,
        }

        st.rerun()