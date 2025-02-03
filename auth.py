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
    # Centraliza o título e a mensagem inicial
    st.markdown(
    """
    <div style="text-align: center; margin-bottom: 1rem;">
        <h2 style="margin-bottom: 0.6rem;">
            🦉<span style="font-weight: 400;">Agenda</span><span style="font-weight: 700;">MCPF</span>
        </h2>
    </div>
    """,
    unsafe_allow_html=True
)


    with st.form(key='login_form'):
        # Campo de email com placeholder de exemplo
        email = st.text_input(
            label="Email",
            placeholder="exemplo@prof.ce.gov.br"
        )

        # Campo de senha com placeholder de exemplo
        senha = st.text_input(
            label="Senha",
            type='password',
            placeholder="Digite sua senha"
        )

        submitted = st.form_submit_button("Login")
        if submitted:
            # Lógica de autenticação (inalterada)
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

    # Mensagem ao final e botão/link para envio de email
    st.markdown(
    """
    <div style="text-align: center; margin-top: 1.5rem;">
        <p style="color: #666; font-size: 0.9rem; margin-bottom: 0.8rem;">
            Em caso de erro, Entre em contato com o administrador do sistema.
        </p>
        
    </div>
    """,
    unsafe_allow_html=True
)


def logout():
    st.session_state["autenticado"] = False
    st.session_state["tipo_usuario"] = None
    st.session_state["email"] = None
    st.session_state["usuario_id"] = None
    st.experimental_rerun()
