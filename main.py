# main.py
import streamlit as st
from auth import verificar_superadmin, criar_superadmin, tela_login
from superadmin import painel_superadmin
from admlab import painel_admin_laboratorio
from professor import painel_professor

def inicializar_sessao():
    """
    Garante que as variáveis de estado necessárias estejam definidas.
    """
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if "tipo_usuario" not in st.session_state:
        st.session_state["tipo_usuario"] = None
    if "email" not in st.session_state:
        st.session_state["email"] = None
    if "usuario_id" not in st.session_state:
        st.session_state["usuario_id"] = None

def exibir_login_ou_painel():
    """
    Verifica se o usuário está autenticado e, caso positivo,
    chama o painel apropriado a partir do tipo de usuário.
    Caso contrário, apresenta a tela de login ou criação de superadmin.
    """
    if not st.session_state["autenticado"]:
        if not verificar_superadmin():
            st.info('Nenhum superadministrador encontrado. Por favor, crie um agora.')
            criar_superadmin()
        else:
            tela_login()
    else:
        painel_map = {
            "superadmin": painel_superadmin,
            "admlab": painel_admin_laboratorio,
            "professor": painel_professor
        }
        tipo_usuario = st.session_state["tipo_usuario"]
        
        if tipo_usuario in painel_map:
            painel_map[tipo_usuario]()
        else:
            st.error("Tipo de usuário desconhecido.")

def main():
    """
    Função principal que organiza o fluxo do sistema.
    """
    inicializar_sessao()
    exibir_login_ou_painel()

if __name__ == "__main__":
    main()
