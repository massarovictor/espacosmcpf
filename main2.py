import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import bcrypt

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar o cliente do Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Função para Autenticar Usuário
def autenticar_usuario(email, senha):
    try:
        # Consultar o usuário pelo email
        response = supabase.table('users').select('*').eq('email', email).execute()
        usuarios = response.data

        if not usuarios:
            return None  # Usuário não encontrado

        usuario = usuarios[0]

        # Verificar a senha usando bcrypt
        hashed_password = usuario['password'].encode('utf-8')
        if bcrypt.checkpw(senha.encode('utf-8'), hashed_password):
            # Retornar as informações do usuário
            return {'tipo_usuario': usuario['tipo_usuario'], 'usuario_id': usuario['id'], 'email': usuario['email']}
        else:
            return None
    except Exception as e:
        st.error(f'Erro ao conectar ao banco de dados: {e}')
        return None

# Tela de Login
def tela_login():
    # Centralizando o título e o formulário de login na página principal
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.title("📅 Sistema de Agendamento de Laboratórios")
        st.write("Por favor, faça login para continuar.")
        st.header("Login")
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            usuario = autenticar_usuario(email, senha)
            if usuario:
                st.session_state["autenticado"] = True
                st.session_state["tipo_usuario"] = usuario['tipo_usuario']
                st.session_state["email"] = usuario['email']
                st.session_state["usuario_id"] = usuario['usuario_id']
                st.success("Login bem-sucedido!")
                st.rerun()
            else:
                st.error("Credenciais inválidas ou erro de conexão. Tente novamente.")

# Função para verificar se o superadmin existe
def verificar_superadmin():
    try:
        response = supabase.table('users').select('*').eq('tipo_usuario', 'superadmin').execute()
        usuarios = response.data
        return len(usuarios) > 0
    except Exception as e:
        st.error(f'Erro ao verificar superadministrador: {e}')
        return False

# Função para criar o superadministrador
def criar_superadmin():
    st.header("Criar Superadministrador")
    with st.form(key='create_superadmin_form'):
        email = st.text_input("Email do Superadministrador")
        senha = st.text_input("Senha", type="password")
        senha_confirmacao = st.text_input("Confirme a Senha", type="password")
        submitted = st.form_submit_button("Criar Superadministrador")

        if submitted:
            if senha != senha_confirmacao:
                st.warning('As senhas não coincidem.')
            elif email.strip() == '' or senha.strip() == '':
                st.warning('Email e senha são obrigatórios.')
            else:
                # Hash da senha
                hashed_password = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                novo_superadmin = {
                    'email': email.strip(),
                    'password': hashed_password,
                    'tipo_usuario': 'superadmin'
                }
                try:
                    response = supabase.table('users').insert(novo_superadmin).execute()
                    st.success('Superadministrador criado com sucesso! Por favor, faça login.')
                    st.rerun()
                except Exception as e:
                    st.error(f'Erro ao criar o superadministrador: {e}')

# Implementar o Painel do Superadministrador
def painel_superadmin():
    st.title("Painel do Superadministrador")
    st.write("Bem-vindo ao painel de administração geral.")

    tab1, tab2 = st.tabs(["Gerenciar Usuários", "Gerenciar Laboratórios"])

    with tab1:
        gerenciar_usuarios()

    with tab2:
        gerenciar_laboratorios()

def gerenciar_usuarios():
    st.subheader("Gerenciar Usuários")

    try:
        # Listar usuários existentes
        response = supabase.table('users').select('id', 'email', 'tipo_usuario').execute()
        usuarios = response.data
        for usuario in usuarios:
            st.write(f"**Email:** {usuario['email']} | **Tipo:** {usuario['tipo_usuario']}")
            if usuario['tipo_usuario'] != 'superadmin':
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Editar", key=f"edit_user_{usuario['id']}"):
                        editar_usuario(usuario)
                with col2:
                    if st.button("Excluir", key=f"delete_user_{usuario['id']}"):
                        excluir_usuario(usuario['id'])

        # Formulário para adicionar um novo usuário
        st.subheader("Adicionar Novo Usuário")
        with st.form(key='add_user_form'):
            novo_email = st.text_input("Email")
            novo_tipo = st.selectbox("Tipo de Usuário", options=['admlab', 'professor'])
            nova_senha = st.text_input("Senha", type='password')
            submitted = st.form_submit_button("Adicionar Usuário")
            if submitted:
                if novo_email.strip() == '' or nova_senha.strip() == '':
                    st.warning('Email e senha são obrigatórios.')
                else:
                    # Hash da senha
                    hashed_password = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    novo_usuario = {
                        'email': novo_email.strip(),
                        'password': hashed_password,
                        'tipo_usuario': novo_tipo
                    }
                    try:
                        response = supabase.table('users').insert(novo_usuario).execute()
                        st.success('Usuário adicionado com sucesso!')
                        st.rerun()
                    except Exception as e:
                        st.error(f'Erro ao adicionar o usuário: {e}')
    except Exception as e:
        st.error(f'Erro ao carregar os usuários: {e}')

def editar_usuario(usuario):
    st.subheader(f"Editar Usuário: {usuario['email']}")
    with st.form(key=f'edit_user_form_{usuario["id"]}'):
        novo_email = st.text_input("Email", value=usuario['email'])
        novo_tipo = st.selectbox("Tipo de Usuário", options=['admlab', 'professor', 'superadmin'], index=['admlab', 'professor', 'superadmin'].index(usuario['tipo_usuario']))
        nova_senha = st.text_input("Senha (deixe em branco para não alterar)", type='password')
        submitted = st.form_submit_button("Salvar Alterações")
        if submitted:
            update_data = {
                'email': novo_email.strip(),
                'tipo_usuario': novo_tipo
            }
            if nova_senha.strip() != '':
                hashed_password = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                update_data['password'] = hashed_password
            try:
                response = supabase.table('users').update(update_data).eq('id', usuario['id']).execute()
                st.success('Usuário atualizado com sucesso!')
                st.rerun()
            except Exception as e:
                st.error(f'Erro ao atualizar o usuário: {e}')

def excluir_usuario(usuario_id):
    if st.confirm('Tem certeza que deseja excluir este usuário? Esta ação não pode ser desfeita.'):
        try:
            response = supabase.table('users').delete().eq('id', usuario_id).execute()
            st.success('Usuário excluído com sucesso!')
            st.rerun()
        except Exception as e:
            st.error(f'Erro ao excluir o usuário: {e}')

def gerenciar_laboratorios():
    st.subheader("Gerenciar Laboratórios")

    try:
        # Listar laboratórios existentes
        response = supabase.table('laboratorios').select('*').execute()
        laboratorios = response.data
        for lab in laboratorios:
            st.write(f"**Nome:** {lab['nome']} | **Descrição:** {lab.get('descricao', '')} | **Capacidade:** {lab.get('capacidade', 'N/A')}")
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
                if st.button("Editar", key=f"edit_lab_{lab['id']}"):
                    editar_laboratorio(lab)
            with col2:
                if st.button("Excluir", key=f"delete_lab_{lab['id']}"):
                    excluir_laboratorio(lab['id'])

        # Formulário para adicionar um novo laboratório
        st.subheader("Adicionar Novo Laboratório")
        with st.form(key='add_lab_form'):
            nome = st.text_input("Nome do Laboratório")
            descricao = st.text_area("Descrição")
            capacidade = st.number_input("Capacidade", min_value=0, step=1)
            # Selecionar um administrador
            try:
                response_admins = supabase.table('users').select('id', 'email').eq('tipo_usuario', 'admlab').execute()
                admin_options = {admin['email']: admin['id'] for admin in response_admins.data} if response_admins.data else {}
            except Exception as e:
                st.error(f'Erro ao carregar administradores: {e}')
                admin_options = {}
            administrador_email = st.selectbox("Administrador do Laboratório (opcional)", options=['Não atribuído'] + list(admin_options.keys()))
            submitted = st.form_submit_button("Adicionar Laboratório")
            if submitted:
                if nome.strip() == '':
                    st.warning('O nome do laboratório é obrigatório.')
                else:
                    administrador_id = admin_options.get(administrador_email) if administrador_email != 'Não atribuído' else None
                    novo_laboratorio = {
                        'nome': nome.strip(),
                        'descricao': descricao.strip(),
                        'capacidade': int(capacidade),
                        'administrador_id': administrador_id
                    }
                    try:
                        response = supabase.table('laboratorios').insert(novo_laboratorio).execute()
                        st.success('Laboratório adicionado com sucesso!')
                        st.rerun()
                    except Exception as e:
                        st.error(f'Erro ao adicionar o laboratório: {e}')
    except Exception as e:
        st.error(f'Erro ao carregar os laboratórios: {e}')

def editar_laboratorio(lab):
    st.subheader(f"Editar Laboratório: {lab['nome']}")
    with st.form(key=f'edit_lab_form_{lab["id"]}'):
        nome = st.text_input("Nome do Laboratório", value=lab['nome'])
        descricao = st.text_area("Descrição", value=lab.get('descricao', ''))
        capacidade = st.number_input("Capacidade", min_value=0, step=1, value=lab.get('capacidade') or 0)
        # Selecionar um administrador
        try:
            response_admins = supabase.table('users').select('id', 'email').eq('tipo_usuario', 'admlab').execute()
            admin_options = {admin['email']: admin['id'] for admin in response_admins.data} if response_admins.data else {}
        except Exception as e:
            st.error(f'Erro ao carregar administradores: {e}')
            admin_options = {}
        current_admin_email = None
        if lab['administrador_id']:
            try:
                response_admin = supabase.table('users').select('email').eq('id', lab['administrador_id']).execute()
                if response_admin.data:
                    current_admin_email = response_admin.data[0]['email']
            except Exception as e:
                st.error(f'Erro ao obter o administrador atual: {e}')
        admin_emails = ['Não atribuído'] + list(admin_options.keys())
        admin_index = admin_emails.index(current_admin_email) if current_admin_email in admin_emails else 0
        administrador_email = st.selectbox("Administrador do Laboratório (opcional)", options=admin_emails, index=admin_index)
        submitted = st.form_submit_button("Salvar Alterações")
        if submitted:
            if nome.strip() == '':
                st.warning('O nome do laboratório é obrigatório.')
            else:
                administrador_id = admin_options.get(administrador_email) if administrador_email != 'Não atribuído' else None
                lab_atualizado = {
                    'nome': nome.strip(),
                    'descricao': descricao.strip(),
                    'capacidade': int(capacidade),
                    'administrador_id': administrador_id
                }
                try:
                    response = supabase.table('laboratorios').update(lab_atualizado).eq('id', lab['id']).execute()
                    st.success('Laboratório atualizado com sucesso!')
                    st.rerun()
                except Exception as e:
                    st.error(f'Erro ao atualizar o laboratório: {e}')

def excluir_laboratorio(lab_id):
    if st.confirm('Tem certeza que deseja excluir este laboratório? Esta ação não pode ser desfeita.'):
        try:
            response = supabase.table('laboratorios').delete().eq('id', lab_id).execute()
            st.success('Laboratório excluído com sucesso!')
            st.rerun()
        except Exception as e:
            st.error(f'Erro ao excluir o laboratório: {e}')

# Implementar o Painel do Administrador de Laboratório
def painel_admin_laboratorio():
    st.title("Painel do Administrador de Laboratório")
    st.write("Bem-vindo ao painel de validação de agendamentos.")

    administrador_id = st.session_state["usuario_id"]

    try:
        # Obter laboratórios associados ao administrador
        response = supabase.table('laboratorios').select('*').eq('administrador_id', administrador_id).execute()
        laboratorios = response.data

        if not laboratorios:
            st.info('Você não está associado a nenhum laboratório.')
            return

        for lab in laboratorios:
            st.subheader(f"Laboratório: {lab['nome']}")
            # Obter agendamentos pendentes para este laboratório
            try:
                response_agendamentos = supabase.table('agendamentos').select('*').eq('laboratorio_id', lab['id']).eq('status', 'pendente').execute()
                agendamentos = response_agendamentos.data
                if not agendamentos:
                    st.info('Nenhum agendamento pendente.')
                else:
                    for agendamento in agendamentos:
                        exibir_agendamento_para_validacao(agendamento)
            except Exception as e:
                st.error(f'Erro ao carregar os agendamentos: {e}')
    except Exception as e:
        st.error(f'Erro ao carregar os laboratórios: {e}')

def exibir_agendamento_para_validacao(agendamento):
    try:
        # Obter informações adicionais
        # Obter nome do professor
        response_user = supabase.table('users').select('email').eq('id', agendamento['usuario_id']).execute()
        professor_email = response_user.data[0]['email'] if response_user.data else 'Desconhecido'

        aulas = [f"{aula}ª Aula" for aula in agendamento['aulas']]
        st.write(f"**Professor:** {professor_email}")
        st.write(f"**Data:** {agendamento['data_agendamento']}")
        st.write(f"**Aulas:** {', '.join(aulas)}")
        st.write(f"**Status:** {agendamento['status']}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Aprovar", key=f"aprovar_{agendamento['id']}"):
                atualizar_status_agendamento(agendamento['id'], 'aprovado')
        with col2:
            if st.button("Rejeitar", key=f"rejeitar_{agendamento['id']}"):
                atualizar_status_agendamento(agendamento['id'], 'rejeitado')
    except Exception as e:
        st.error(f'Erro ao exibir agendamento: {e}')

def atualizar_status_agendamento(agendamento_id, novo_status):
    try:
        response = supabase.table('agendamentos').update({'status': novo_status}).eq('id', agendamento_id).execute()
        st.success(f'Agendamento {novo_status} com sucesso!')
        st.rerun()
    except Exception as e:
        st.error(f'Erro ao atualizar o status do agendamento: {e}')

# Implementar o Painel do Professor
def painel_professor():
    st.title("Painel do Professor")
    st.write("Bem-vindo ao painel de agendamento de laboratórios.")

    tab1, tab2, tab3 = st.tabs(["Agendar Laboratório", "Meus Agendamentos", "Agendamentos do Laboratório"])

    with tab1:
        agendar_laboratorio()

    with tab2:
        listar_agendamentos_professor()

    with tab3:
        visualizar_agendamentos_laboratorio()

def agendar_laboratorio():
    st.subheader("Agendar um Laboratório")
    try:
        # Obter laboratórios disponíveis
        response = supabase.table('laboratorios').select('id', 'nome').execute()
        laboratorios = response.data
        if not laboratorios:
            st.error('Nenhum laboratório disponível.')
            return
        lab_options = {lab['nome']: lab['id'] for lab in laboratorios}
        lab_nome = st.selectbox("Escolha o Laboratório", options=list(lab_options.keys()))
        laboratorio_id = lab_options[lab_nome]

        data_agendamento = st.date_input("Data do Agendamento")

        # Definir os períodos de aula
        aulas_opcoes = [1,2,3,4,5,6,7,8,9]
        aulas_selecionadas = st.multiselect("Selecione a(s) aula(s) para agendamento", aulas_opcoes)

        if st.button("Confirmar Agendamento"):
            if aulas_selecionadas:
                # Verificar disponibilidade
                if verificar_disponibilidade(laboratorio_id, data_agendamento, aulas_selecionadas):
                    confirmar_agendamento_professor(laboratorio_id, data_agendamento, aulas_selecionadas)
                else:
                    st.error('O laboratório não está disponível nas aulas selecionadas.')
            else:
                st.warning("Por favor, selecione pelo menos uma aula para agendamento.")
    except Exception as e:
        st.error(f'Erro ao agendar laboratório: {e}')

def verificar_disponibilidade(laboratorio_id, data_agendamento, aulas_numeros):
    try:
        # Verificar horários fixos
        dia_semana = data_agendamento.weekday()  # 0 (Segunda-feira) a 6 (Domingo)
        response_horarios_fixos = supabase.table('horarios_fixos').select('*').eq('laboratorio_id', laboratorio_id).eq('dia_semana', dia_semana).execute()
        horarios_fixos = response_horarios_fixos.data
        for horario_fixo in horarios_fixos:
            aulas_fixas = horario_fixo['aulas']
            if any(aula in aulas_numeros for aula in aulas_fixas):
                return False  # Conflito com horário fixo

        # Verificar agendamentos aprovados existentes
        response_agendamentos = supabase.table('agendamentos').select('*').eq('laboratorio_id', laboratorio_id).eq('data_agendamento', data_agendamento.isoformat()).eq('status', 'aprovado').execute()
        agendamentos_existentes = response_agendamentos.data
        for agendamento in agendamentos_existentes:
            aulas_agendadas = agendamento['aulas']
            if any(aula in aulas_numeros for aula in aulas_agendadas):
                return False  # Conflito com outro agendamento
        return True  # Disponível
    except Exception as e:
        st.error(f'Erro ao verificar disponibilidade: {e}')
        return False

def confirmar_agendamento_professor(laboratorio_id, data_agendamento, aulas_selecionadas):
    usuario_id = st.session_state["usuario_id"]
    novo_agendamento = {
        'usuario_id': usuario_id,
        'laboratorio_id': laboratorio_id,
        'data_agendamento': data_agendamento.isoformat(),
        'aulas': aulas_selecionadas,
        'status': 'pendente'
    }
    try:
        response = supabase.table('agendamentos').insert(novo_agendamento).execute()
        st.success('Agendamento solicitado com sucesso! Aguardando aprovação.')
    except Exception as e:
        st.error(f'Erro ao salvar o agendamento: {e}')

def listar_agendamentos_professor():
    st.subheader("Meus Agendamentos")
    usuario_id = st.session_state["usuario_id"]
    try:
        response = supabase.table('agendamentos').select('*').eq('usuario_id', usuario_id).execute()
        agendamentos = response.data
        if not agendamentos:
            st.info('Você não possui agendamentos.')
        else:
            for agendamento in agendamentos:
                # Obter nome do laboratório
                response_lab = supabase.table('laboratorios').select('nome').eq('id', agendamento['laboratorio_id']).execute()
                lab_nome = response_lab.data[0]['nome'] if response_lab.data else 'Desconhecido'
                aulas = [f"{aula}ª Aula" for aula in agendamento['aulas']]
                st.write(f"📅 **Data:** {agendamento['data_agendamento']} | **Laboratório:** {lab_nome} | **Aulas:** {', '.join(aulas)} | **Status:** {agendamento['status']}")
    except Exception as e:
        st.error(f'Erro ao carregar seus agendamentos: {e}')

def visualizar_agendamentos_laboratorio():
    st.subheader("Agendamentos do Laboratório")
    try:
        # Selecionar laboratório
        response_labs = supabase.table('laboratorios').select('id', 'nome').execute()
        laboratorios = response_labs.data
        if not laboratorios:
            st.error('Nenhum laboratório disponível.')
            return
        lab_options = {lab['nome']: lab['id'] for lab in laboratorios}
        lab_nome = st.selectbox("Escolha o Laboratório", options=list(lab_options.keys()))
        laboratorio_id = lab_options[lab_nome]

        response_agendamentos = supabase.table('agendamentos').select('*').eq('laboratorio_id', laboratorio_id).execute()
        agendamentos = response_agendamentos.data
        if not agendamentos:
            st.info('Não há agendamentos para este laboratório.')
        else:
            for agendamento in agendamentos:
                # Obter email do professor
                response_user = supabase.table('users').select('email').eq('id', agendamento['usuario_id']).execute()
                professor_email = response_user.data[0]['email'] if response_user.data else 'Desconhecido'
                aulas = [f"{aula}ª Aula" for aula in agendamento['aulas']]
                st.write(f"**Professor:** {professor_email} | **Data:** {agendamento['data_agendamento']} | **Aulas:** {', '.join(aulas)} | **Status:** {agendamento['status']}")
    except Exception as e:
        st.error(f'Erro ao carregar agendamentos do laboratório: {e}')

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
    # Exibindo um menu na barra lateral
    with st.sidebar:
        st.header("Menu")
        if st.button("Logout"):
            st.session_state["autenticado"] = False
            st.session_state["tipo_usuario"] = None
            st.session_state["email"] = None
            st.session_state["usuario_id"] = None
            st.rerun()

    tipo_usuario = st.session_state["tipo_usuario"]
    if tipo_usuario == "superadmin":
        painel_superadmin()
    elif tipo_usuario == "admlab":
        painel_admin_laboratorio()
    elif tipo_usuario == "professor":
        painel_professor()
    else:
        st.error("Tipo de usuário desconhecido.")
