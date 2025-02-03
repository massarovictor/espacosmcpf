# components/dialogs.py
import streamlit as st

def confirm_dialog(title: str, message: str, on_confirm):
    if st.button("Confirmar"):
        on_confirm()
    st.info(f"{title}: {message}")
