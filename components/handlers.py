# components/handlers.py
import streamlit as st
from functools import wraps

def error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"Erro: {e}")
    return wrapper

def success_message(message: str):
    st.success(message)
