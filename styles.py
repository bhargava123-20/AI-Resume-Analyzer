import streamlit as st

def apply_custom_styles():
    st.markdown("""
    <style>
    .stApp {
        background-color: white;
    }
    </style>
    """, unsafe_allow_html=True)