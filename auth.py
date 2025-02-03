import streamlit as st
import bcrypt
import re
from database import supabase  # Ajuste conforme sua conexão/credenciais

def aplicar_estilos():
    """
    Aplica estilos customizados para o layout do Streamlit.
    """
    st.markdown(
        """
        <style>
            /* Layout principal */
            .main {
                padding: 2rem 1rem 4rem;
                background-color: #f8f9fa;
            }
            
            /* Título e cabeçalho */
            .header {
                text-align: center;
                margin-bottom: 1rem;
            }

            /* Subtítulo (abaixo do cabeçalho) */
            .subheader {
                text-align: center;
                margin-bottom: 2rem;
                color: #444;
            }

            /* Formulário */
            [data-testid="stForm"] {
                border: 1px solid #e5e7eb;
                border-radius: 0.5rem;
                padding: 2rem;
                background-color: #fff;
                max-width: 400px;
                margin: 0 auto; /* Centraliza o formulário */
            }

            /* Caixa de mensagem de erro */
            .error-box {
                padding: 1rem;
                border-radius: 0.5rem;
                background: #fee2e2;
                color: #991b1b;
                margin-bottom: 1rem;
            }

            /* Caixa de mensagem de sucesso */
            .success-box {
                padding: 1rem;
                border-radius: 0.5rem;
                background: #dcfce7;
                color: #166534;
                margin-bottom: 1rem;
            }

            /* Botões */
            .stButton>button {
                width: 100%;
                transition: all 0.3s ease;
                color: #fff;
                background-color: #2c3e50;
                border: none;
                font-size: 1rem;
                padding: 0.75rem;
                border-radius: 0.5rem;
                font-weight: 500;
            }
            .stButton>button:hover {
                transform: scale(1.02);
                background-color: #34495e;
            }

            /* Texto de aviso */
            .aviso-acesso {
                text-align: center;
                margin-top: 1.5rem;
                color: #666;
                font-size: 0.9em;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

def verificar_superadmin():
    """Verifica a existência de pelo menos um superadmin no banco."""
    try:
        response = supabase.table('users').select('*').eq('tipo_usuario', 'superadmin').execute()
        return len(response.data or []) > 0
    except Exception as e:
        st.error(f"Erro ao verificar superadmin: {str(e)}")
        return False

def criar_superadmin():
    """
    Caso não exista nenhum superadmin, implemente aqui a criação de um usuário superadmin.
    Esta função é apenas um placeholder, ajuste conforme sua regra.
    """
    st.warning("Nenhum superadmin encontrado. Implemente a lógica de criação de superadmin.")

def autenticar_usuario(email, senha):
    """Autentica usuário no banco de dados."""
    try:
        response = supabase.table('users').select('*').eq('email', email.strip().lower()).execute()
        if response.data:
            usuario = response.data[0]
            if bcrypt.checkpw(senha.encode('utf-8'), usuario['password'].encode('utf-8')):
                return usuario
        return None
    except Exception as e:
        st.error(f"Erro de autenticação: {str(e)}")
        return None

def atualizar_sessao(usuario):
    """Atualiza os dados da sessão."""
    st.session_state.update({
        "autenticado": True,
        "tipo_usuario": usuario['tipo_usuario'],
        "email": usuario['email'],
        "usuario_id": usuario['id']
    })

def tela_login():
    """
    Interface de login. 
    Mostra o emoji da coruja seguido de 'Agenda' em regular e 'MCPF' em negrito no título,
    e a escola em fonte menor abaixo, tudo centralizado.
    """
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 3rem;">
                🦉<span style="font-weight: 400;">Agenda</span><span style="font-weight: 700;">MCPF</span>
            </div>
            
        </div>
        """,
        unsafe_allow_html=True
    )

    # Linha divisória para organização
    st.divider()

    # Formulário de login
    with st.form(key='form_login'):
        st.subheader("Acesso ao Sistema")

        email = st.text_input(
            "Email institucional",
            placeholder="exemplo@prof.ce.gov.br",
            help="Utilize o email fornecido pela instituição"
        )

        senha = st.text_input(
            "Senha de acesso",
            type='password',
            placeholder="Digite sua senha"
        )

        if st.form_submit_button("Entrar"):
            with st.spinner("Verificando credenciais..."):
                usuario = autenticar_usuario(email, senha)
                if usuario:
                    atualizar_sessao(usuario)
                    st.success("Autenticação realizada com sucesso!")
                    st.experimental_rerun()
                else:
                    st.error("Credenciais inválidas ou usuário não encontrado")

    # Mensagem de orientação para recuperar acesso
    st.markdown(
        '''
        <div class="aviso-acesso">
        Em caso de erro no acesso entre em contato com o administrador do sistema<br>
        </div>
        ''',
        unsafe_allow_html=True
    )

def main():
    aplicar_estilos()

    if not verificar_superadmin():
        criar_superadmin()
    else:
        if not st.session_state.get("autenticado"):
            tela_login()
        else:
            st.success("Você já está autenticado!")
            if st.button("Ir para o Dashboard"):
                # Lógica futura de navegação para o Dashboard
                pass

if __name__ == "__main__":
    main()
