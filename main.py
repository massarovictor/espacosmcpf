# main.py
import streamlit as st
from auth import verificar_superadmin, criar_superadmin, tela_login
from superadmin import painel_superadmin
from admlab import painel_admin_laboratorio
from professor import painel_professor

# Inicialização da sessão
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["tipo_usuario"] = None
    st.session_state["email"] = None
    st.session_state["usuario_id"] = None

# Exibir tela de login ou o painel apropriado
if not st.session_state["autenticado"]:
    if not verificar_superadmin():
        st.info('Nenhum superadministrador encontrado. Por favor, crie um agora.')
        criar_superadmin()
    else:
        tela_login()
else:
    tipo_usuario = st.session_state["tipo_usuario"]
    if tipo_usuario == "superadmin":
        painel_superadmin()
    elif tipo_usuario == "admlab":
        painel_admin_laboratorio()
    elif tipo_usuario == "professor":
        painel_professor()
    else:
        st.error("Tipo de usuário desconhecido.")
