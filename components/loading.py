# components/loading.py
import streamlit as st
from contextlib import contextmanager

@contextmanager
def loading_spinner():
    with st.spinner("Carregando..."):
        yield
