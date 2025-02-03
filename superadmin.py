import streamlit as st
import bcrypt
from database import supabase
from components import (
    loading_spinner,
    confirm_dialog,
    error_handler,
    success_message
)

def logout():
    """
    Botão de logout: limpa as variáveis de sessão e força recarregamento.
    """
    st.session_state["autenticado"] = False
    st.session_state["tipo_usuario"] = None
    st.session_state["email"] = None
    st.session_state["usuario_id"] = None
    st.experimental_rerun()

# =============================================================================
#                           PAINEL SUPERADMIN
# =============================================================================

def painel_superadmin():
    """
    Exibe o painel principal do superadmin, contendo as abas de 
    gestão de usuários e de laboratórios.
    Agora, sem o botão de refresh, e com o botão de logout no final.
    """
    # Cabeçalho inicial (nome do sistema)
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
    
    # Subtítulo ou título secundário
    st.subheader("Gestão Integrada de Recursos")

    # Criação das abas de Usuários e Laboratórios
    tab1, tab2 = st.tabs(["👥 Gestão de Usuários", "🔬 Gestão de Laboratórios"])
    
    with tab1:
        with loading_spinner():
            gerenciar_usuarios()
    
    with tab2:
        with loading_spinner():
            gerenciar_laboratorios()

    # Linha divisória e botão de logout no final
    st.divider()
    if st.button("Logout", help="Encerrar sessão"):
        logout()

# =============================================================================
#                            GESTÃO DE USUÁRIOS
# =============================================================================

def gerenciar_usuarios():
    """
    Exibe a interface para:
    - Adicionar novo usuário
    - Listar usuários (exceto superadmin)
    - Pesquisar por email
    - Editar e excluir usuários
    """
    todos_usuarios = carregar_usuarios() or []
    # Filtra para não incluir superadmins
    usuarios = [u for u in todos_usuarios if u['tipo_usuario'] != 'superadmin']
    
    with st.expander("➕ Novo Usuário", expanded=True):
        adicionar_usuario()

    st.subheader("📋 Lista de Usuários")
    if not usuarios:
        return st.info("Nenhum usuário cadastrado.", icon="ℹ️")

    # Campo de pesquisa
    search_query = st.text_input("🔍 Pesquisar usuário por email...")
    search_query_lower = search_query.lower().strip()
    filtered_users = [u for u in usuarios if search_query_lower in u['email'].lower()]
    
    # Exibir lista de usuários em expansores
    for usuario in filtered_users:
        with st.expander(f"{usuario['email']} ({usuario['tipo_usuario']})"):
            col1, col2 = st.columns([3, 1])
            with col1:
                exibir_detalhes_usuario(usuario)
            with col2:
                # Botões de Editar e Excluir
                if st.button("✏️ Editar", key=f"edit_{usuario['id']}"):
                    st.session_state['editar_usuario'] = usuario
                if st.button("🗑️ Excluir", key=f"del_{usuario['id']}"):
                    confirm_dialog(
                        title="Confirmação de Exclusão",
                        message=f"Excluir usuário {usuario['email']}?",
                        on_confirm=lambda: excluir_usuario(usuario['id'])
                    )

    # Exibir formulário de edição, se selecionado
    if "editar_usuario" in st.session_state:
        editar_usuario(st.session_state['editar_usuario'])

def carregar_usuarios():
    """
    Carrega todos os usuários do banco (sem cache)
    para que a lista seja sempre atualizada.
    """
    return supabase.table('users').select('id, email, tipo_usuario').execute().data

def exibir_detalhes_usuario(usuario):
    """
    Exibe informações do usuário (email, tipo, etc.).
    Pode ser expandido para mais detalhes, se existirem no banco.
    """
    st.write(f"**Email:** {usuario['email']}")
    st.write(f"**Tipo de Usuário:** {usuario['tipo_usuario']}")

def adicionar_usuario():
    """
    Mostra um formulário para criar um novo usuário com email, tipo e senha.
    """
    with st.form(key='form_adicionar_usuario'):
        email = st.text_input("Email:")
        tipo_usuario = st.radio("Tipo de usuário:", ['admlab', 'professor'])
        senha = st.text_input("Senha:", type="password")
        senha_confirmacao = st.text_input("Confirme a senha:", type="password")
        
        if st.form_submit_button("Salvar"):
            if not email.strip() or not senha.strip():
                st.warning("Email e senha são obrigatórios!")
            elif senha != senha_confirmacao:
                st.warning("As senhas não conferem!")
            else:
                criar_usuario(email, senha, tipo_usuario)
                st.experimental_rerun()

@error_handler
def criar_usuario(email, senha, tipo_usuario):
    """
    Cria um novo registro de usuário no Supabase.
    Verifica se o email já existe, caso sim, exibe aviso e não faz o insert.
    """
    # Verificar duplicidade de email
    existente = supabase.table('users').select('id').eq('email', email.strip()).execute().data
    if existente:
        st.warning("O usuário já existe no banco de dados. Defina outro e-mail.")
        return

    hashed_password = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    novo_usuario = {
        'email': email.strip(),
        'password': hashed_password,
        'tipo_usuario': tipo_usuario
    }
    supabase.table('users').insert(novo_usuario).execute()
    success_message("Usuário criado com sucesso!")

def editar_usuario(usuario):
    """
    Exibe um formulário para editar os dados de um usuário existente,
    incluindo possibilidade de mudar senha e tipo de usuário.
    """
    st.subheader(f"Editando Usuário: {usuario['email']}")
    with st.form(key=f"form_editar_usuario_{usuario['id']}"):
        email_novo = st.text_input("Email:", value=usuario['email'])
        tipo_novo = st.radio(
            "Tipo de usuário:",
            ['admlab','professor'],
            index=['admlab','professor'].index(usuario['tipo_usuario'])
            if usuario['tipo_usuario'] in ['admlab','professor'] else 0
        )
        senha_nova = st.text_input("Nova senha (opcional):", type="password")
        senha_confirma = st.text_input("Confirme a nova senha:", type="password")
        
        if st.form_submit_button("Atualizar"):
            if senha_nova and senha_nova != senha_confirma:
                st.warning("As senhas não conferem!")
            else:
                atualizar_usuario(usuario['id'], email_novo, tipo_novo, senha_nova)
                st.experimental_rerun()

@error_handler
def atualizar_usuario(usuario_id, email_novo, tipo_novo, senha_nova=None):
    """
    Atualiza os dados do usuário no Supabase.
    Se a senha_nova for informada, também atualiza a senha (hashed).
    """
    update_data = {
        'email': email_novo.strip(),
        'tipo_usuario': tipo_novo
    }
    if senha_nova:
        hashed = bcrypt.hashpw(senha_nova.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        update_data['password'] = hashed
    
    supabase.table('users').update(update_data).eq('id', usuario_id).execute()
    
    # Ao término da edição, remover chave do st.session_state para não reabrir formulário
    if 'editar_usuario' in st.session_state:
        del st.session_state['editar_usuario']
    
    success_message("Usuário atualizado com sucesso!")

@error_handler
def excluir_usuario(usuario_id):
    """
    Exclui um usuário do Supabase a partir de seu ID. 
    Em caso de sucesso, exibe mensagem de sucesso e recarrega a tela.
    """
    supabase.table('users').delete().eq('id', usuario_id).execute()
    success_message("Usuário excluído com sucesso!")
    
    # Se o usuário em edição for o mesmo excluído, remove do session_state
    if 'editar_usuario' in st.session_state and st.session_state['editar_usuario']['id'] == usuario_id:
        del st.session_state['editar_usuario']
    
    st.experimental_rerun()

# =============================================================================
#                            GESTÃO DE LABORATÓRIOS
# =============================================================================

def gerenciar_laboratorios():
    """
    Exibe a gestão de laboratórios (listar, criar, editar e excluir).
    """
    st.subheader("Gestão de Laboratórios")
    
    # Carregar laboratórios diretamente (sem cache)
    laboratorios = carregar_labs() or []
    
    # Formulário para adicionar novo laboratório
    with st.expander("➕ Novo Laboratório", expanded=True):
        adicionar_laboratorio_form()
    
    # Listar laboratórios existentes
    st.subheader("📋 Lista de Laboratórios")
    if not laboratorios:
        st.info("Nenhum laboratório cadastrado.")
        return
    
    # Campo de pesquisa (opcional)
    search_query = st.text_input("🔍 Pesquisar por nome do laboratório...")
    search_query_lower = search_query.lower().strip()
    filtered_labs = [lab for lab in laboratorios if search_query_lower in lab['nome'].lower()]
    
    # Exibir lista de laboratórios em expansores
    for lab in filtered_labs:
        with st.expander(f"{lab['nome']}"):
            st.write(f"**ID:** {lab['id']}")
            st.write(f"**Descrição:** {lab.get('descricao','N/A')}")
            st.write(f"**Capacidade:** {lab.get('capacidade','N/A')}")
            st.write(f"**Administrador:** {lab.get('administrador_id','Não atribuído')}")

            col1, col2 = st.columns([3, 1])
            with col1:
                st.write("Detalhes adicionais se houver...")
            with col2:
                if st.button("✏️ Editar", key=f"edit_lab_{lab['id']}"):
                    st.session_state['editar_laboratorio'] = lab
                if st.button("🗑️ Excluir", key=f"del_lab_{lab['id']}"):
                    confirm_dialog(
                        title="Confirmação de Exclusão",
                        message=f"Excluir laboratório {lab['nome']}?",
                        on_confirm=lambda: excluir_laboratorio(lab['id'])
                    )
    
    # Se for necessário editar um laboratório, exiba o formulário
    if 'editar_laboratorio' in st.session_state:
        editar_laboratorio_form(st.session_state['editar_laboratorio'])

def carregar_labs():
    """
    Carrega todos os laboratórios do banco (sem cache),
    para que fiquem sempre atualizados.
    """
    return supabase.table('laboratorios').select('*').execute().data

def adicionar_laboratorio_form():
    """
    Exibe um formulário para criar um novo laboratório.
    Ajuste o nome dos campos de acordo com a estrutura do seu banco.
    """
    with st.form(key='form_adicionar_laboratorio'):
        nome = st.text_input("Nome do Laboratório:")
        descricao = st.text_area("Descrição:")
        capacidade = st.number_input("Capacidade:", min_value=0, step=1)
        
        # Caso queira associar a um administrador específico (opcional)
        st.write("Selecione o administrador responsável (opcional):")
        admins = [u for u in carregar_usuarios() if u['tipo_usuario'] == 'admlab']
        admin_map = {adm['email']: adm['id'] for adm in admins}
        admin_emails = list(admin_map.keys())
        admin_emails.insert(0, "Não atribuído")  # Opção para não atribuir
        admin_escolhido = st.selectbox("Administrador:", admin_emails, index=0)
        
        if st.form_submit_button("Salvar"):
            if not nome.strip():
                st.warning("O nome do laboratório é obrigatório!")
            else:
                if admin_escolhido != "Não atribuído":
                    administrador_id = admin_map[admin_escolhido]
                else:
                    administrador_id = None
                
                criar_laboratorio(nome.strip(), descricao.strip(), capacidade, administrador_id)
                st.experimental_rerun()

@error_handler
def criar_laboratorio(nome, descricao, capacidade, administrador_id):
    """
    Cria um novo laboratório no Supabase.
    """
    novo_lab = {
        'nome': nome,
        'descricao': descricao,
        'capacidade': capacidade,
        'administrador_id': administrador_id
    }
    supabase.table('laboratorios').insert(novo_lab).execute()
    success_message("Laboratório criado com sucesso!")

def editar_laboratorio_form(lab):
    """
    Exibe um formulário para editar os dados de um laboratório existente.
    """
    st.subheader(f"Editando Laboratório: {lab['nome']}")
    with st.form(key=f"form_editar_lab_{lab['id']}"):
        nome_novo = st.text_input("Nome do Laboratório:", value=lab['nome'])
        descricao_nova = st.text_area("Descrição:", value=lab.get('descricao',''))
        capacidade_nova = st.number_input("Capacidade:", value=lab.get('capacidade', 0), step=1)
        
        # Selecionar administrador responsável
        admins = [u for u in carregar_usuarios() if u['tipo_usuario'] == 'admlab']
        admin_map = {adm['email']: adm['id'] for adm in admins}
        admin_emails = list(admin_map.keys())
        admin_emails.insert(0, "Não atribuído")
        
        # Descobrir o email atual do administrador
        admin_atual_email = None
        if lab.get('administrador_id'):
            resp_admin = supabase.table('users').select('email').eq('id', lab['administrador_id']).execute().data
            if resp_admin:
                admin_atual_email = resp_admin[0]['email']
        
        # Se não houver admin_atual_email, usar "Não atribuído" como default
        if admin_atual_email and admin_atual_email in admin_emails:
            index_admin = admin_emails.index(admin_atual_email)
        else:
            index_admin = 0
        
        admin_escolhido = st.selectbox("Administrador:", admin_emails, index=index_admin)
        
        if st.form_submit_button("Atualizar"):
            if not nome_novo.strip():
                st.warning("O nome do laboratório é obrigatório!")
            else:
                if admin_escolhido != "Não atribuído":
                    administrador_id = admin_map[admin_escolhido]
                else:
                    administrador_id = None
                
                atualizar_laboratorio(
                    lab['id'],
                    nome_novo.strip(),
                    descricao_nova.strip(),
                    capacidade_nova,
                    administrador_id
                )
                st.experimental_rerun()

@error_handler
def atualizar_laboratorio(lab_id, nome, descricao, capacidade, administrador_id):
    """
    Atualiza os dados de um laboratório no Supabase.
    """
    update_data = {
        'nome': nome,
        'descricao': descricao,
        'capacidade': capacidade,
        'administrador_id': administrador_id
    }
    supabase.table('laboratorios').update(update_data).eq('id', lab_id).execute()
    
    if 'editar_laboratorio' in st.session_state:
        del st.session_state['editar_laboratorio']
    
    success_message("Laboratório atualizado com sucesso!")

@error_handler
def excluir_laboratorio(lab_id):
    """
    Exclui um laboratório do Supabase a partir de seu ID. 
    Em caso de sucesso, exibe mensagem de sucesso e recarrega a página.
    """
    supabase.table('laboratorios').delete().eq('id', lab_id).execute()
    success_message("Laboratório excluído com sucesso!")
    
    if 'editar_laboratorio' in st.session_state and st.session_state['editar_laboratorio']['id'] == lab_id:
        del st.session_state['editar_laboratorio']
    
    st.experimental_rerun()
