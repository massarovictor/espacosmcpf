# superadmin.py
import streamlit as st
import bcrypt
import pandas as pd
from lab_crud import adicionar_novo_laboratorio, confirmar_exclusao_laboratorio, editar_laboratorio
from user_crud import adicionar_usuario, confirmar_exclusao_usuario, editar_usuario
from database import supabase

def painel_superadmin():
    st.title("🦉AgendaMCPF")  # Título do sistema


    st.subheader("Painel de Administração Geral")
    st.write("**EEEP Professora Maria Célia Pinheiro Falcão**")  # Nome da escola
    st.markdown("---")  # Linha separadora para organizar o layout
    tab1, tab2 = st.tabs(["Gerenciar Usuários", "Gerenciar Espaços"])

    with tab1:
        gerenciar_usuarios()

    with tab2:
        gerenciar_laboratorios()


def gerenciar_usuarios():
    st.subheader("Adicionar Novo Usuário")
    adicionar_usuario()
    
    st.subheader("Usuários Cadastrados")
    try:
        # Listar usuários existentes
        response = supabase.table('users').select('id', 'name', 'email', 'tipo_usuario').execute()
        usuarios = response.data
        if not usuarios:
            st.info("Nenhum usuário cadastrado.")
            return
        else:
            for usuario in usuarios:
                if usuario['tipo_usuario'] != 'superadmin':
                    with st.expander(f"{usuario['name'] or usuario['email']} - {usuario['tipo_usuario']}"):
                        if st.button("📝 Editar Usuário", key=f"edit_user_{usuario['id']}"):
                            st.session_state['editar_usuario'] = usuario
                            st.rerun()


                        if st.button("❌ Excluir Usuário", key=f"delete_user_{usuario['id']}"):
                            st.session_state['confirm_delete_user_id'] = usuario['id']
                            st.rerun()

                        if st.session_state.get('editar_usuario') and st.session_state['editar_usuario']['id'] == usuario['id']:
                            editar_usuario(st.session_state['editar_usuario'])

        # Inicializar o estado se necessário
        if 'confirm_delete_user_id' not in st.session_state:
            st.session_state['confirm_delete_user_id'] = None

        if st.session_state['confirm_delete_user_id']:
            # Exibir a confirmação de exclusão
            confirmar_exclusao_usuario(st.session_state['confirm_delete_user_id'])

        if 'editar_usuario' not in st.session_state:
            st.session_state['editar_usuario'] = None
        

    except Exception as e:
        st.error(f'Erro ao carregar os usuários: {e}')



def gerenciar_laboratorios():
    st.subheader("Adicionar Novo Espaço")
    adicionar_novo_laboratorio()
    
    st.subheader("Espaços Cadastrados")
    try:
        response = supabase.table('laboratorios').select('*').execute()
        laboratorios = response.data

        # Inicializar o estado se necessário
        if 'confirm_delete_lab_id' not in st.session_state:
            st.session_state['confirm_delete_lab_id'] = None

        if st.session_state['confirm_delete_lab_id']:
            # Exibir a confirmação de exclusão
            confirmar_exclusao_laboratorio(st.session_state['confirm_delete_lab_id'])

        if not laboratorios:
            st.info("Nenhum Espaço cadastrado.")

            return
        
        for lab in laboratorios:
            with st.expander(f"{lab['nome']}"):
                st.write(f"**Descrição:** {lab.get('descricao', '')}")
                st.write(f"**Capacidade:** {lab.get('capacidade', 'N/A')}")
                
                # Obter o email do administrador
                admin_email = 'Não atribuído'
                if lab['administrador_id']:
                    try:
                        response_admin = supabase.table('users').select('email').eq('id', lab['administrador_id']).execute()
                        if response_admin.data:
                            admin_email = response_admin.data[0]['email']
                    except Exception as e:
                        st.error(f'Erro ao obter o administrador: {e}')
                st.write(f"**Administrador:** {admin_email}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📝 Editar Laboratório", key=f"edit_lab_{lab['id']}"):
                        st.session_state['editar_laboratorio'] = lab  # Armazena o laboratório a ser editado
                        st.session_state['editando'] = True  # Indica que está em modo de edição
                    
                with col2:
                    if st.button("❌ Excluir Laboratório", key=f"delete_lab_{lab['id']}"):
                        st.session_state['confirm_delete_lab_id'] = lab['id']
                        st.rerun()
                
                # Se estiver editando, exibe o formulário de edição
                if st.session_state.get('editando') and st.session_state['editar_laboratorio']['id'] == lab['id']:
                    editar_laboratorio(st.session_state['editar_laboratorio'])  # Chama a função de edição

    except Exception as e:
        st.error(f'Erro ao carregar os laboratórios: {e}')




