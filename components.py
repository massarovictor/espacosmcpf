import streamlit as st

def logout_button():
    if st.button("Logout"):
        st.session_state["autenticado"] = False
        st.session_state["tipo_usuario"] = None
        st.session_state["email"] = None
        st.session_state["usuario_id"] = None
        st.rerun()
