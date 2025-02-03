# auth.py
import streamlit as st
import bcrypt
from database import supabase
def verificar_superadmin():
    try:
        response = supabase.table('users').select('*').eq('tipo_usuario', 'superadmin').execute()
        if response.data:
            return True
        else:
            return False
    except Exception as e:
        st.error(f"Erro ao verificar o superadministrador: {e}")
        return False
def criar_superadmin():
    st.title("Criar Superadministrador")
    with st.form(key='create_superadmin_form'):
        email = st.text_input("Email")
        senha = st.text_input("Senha", type='password')
        senha_confirmacao = st.text_input("Confirme a Senha", type='password')
        submitted = st.form_submit_button("Criar Superadministrador")
        if submitted:
            if senha != senha_confirmacao:
                st.warning('As senhas não coincidem.')
            elif email.strip() == '' or senha.strip() == '':
                st.warning('Email e senha são obrigatórios.')
            else:
                hashed_password = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                novo_usuario = {
                    'email': email.strip(),
                    'password': hashed_password,
                    'tipo_usuario': 'superadmin'
                }
                try:
                    response = supabase.table('users').insert(novo_usuario).execute()
                    st.success('Superadministrador criado com sucesso! Por favor, faça login.')
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f'Erro ao criar o superadministrador: {e}')
def tela_login():
    st.title("📅 LabManager")  # Título do sistema
    st.subheader("Sistema de Agendamento de Laboratórios")  # Nome da escola
    st.write("**EEEP Professora Maria Célia Pinheiro Falcão**")  # Nome da escola
    st.markdown("---")  # Linha separadora para organizar o layout
    st.write("Por favor, faça o login para acessar o sistema.")
    with st.form(key='login_form'):
        email = st.text_input("Email")
        senha = st.text_input("Senha", type='password')
        submitted = st.form_submit_button("Login")
        if submitted:
            # Realizar autenticação
            try:
                response = supabase.table('users').select('*').eq('email', email.strip()).execute()
                if response.data:
                    usuario = response.data[0]
                    if bcrypt.checkpw(senha.encode('utf-8'), usuario['password'].encode('utf-8')):
                        st.session_state["autenticado"] = True
                        st.session_state["tipo_usuario"] = usuario['tipo_usuario']
                        st.session_state["email"] = usuario['email']
                        st.session_state["usuario_id"] = usuario['id']
                        st.success("Login realizado com sucesso!")
                        st.experimental_rerun()
                    else:
                        st.error("Email ou senha incorretos.")
                else:
                    st.error("Email ou senha incorretos.")
            except Exception as e:
                st.error(f"Erro ao realizar o login: {e}")
def logout():
    st.session_state["autenticado"] = False
    st.session_state["tipo_usuario"] = None
    st.session_state["email"] = None
    st.session_state["usuario_id"] = None
    st.experimental_rerun()
