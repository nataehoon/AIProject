import streamlit as st
from services.medical_service import MedicalService

st.set_page_config(
    page_title="MRI Parsing Engine",
    page_icon="📊",
    layout="wide"
)

with st.spinner():
    raw_data_list = MedicalService.get_raw_data()

    qa_list, paper_list = raw_data_list
    version = [qa for qa in dict.fromkeys(qa.version for qa in qa_list)]