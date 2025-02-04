# superadmin.py
import streamlit as st
import bcrypt
import pandas as pd
from user_crud import adicionar_usuario, confirmar_exclusao_usuario, editar_usuario
from database import supabase

def painel_superadmin():
    st.title("📅 Espaços MCPF")  # Título do sistema


    st.subheader("Painel de Administração Geral")
    st.write("**EEEP Professora Maria Célia Pinheiro Falcão**")  # Nome da escola
    st.markdown("---")  # Linha separadora para organizar o layout
    tab1, tab2 = st.tabs(["Gerenciar Usuários", "Gerenciar Laboratórios"])

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
    st.subheader("Adicionar Novo Laboratório")
    adicionar_novo_laboratorio()
    
    st.subheader("Laboratórios Cadastrados")
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
            st.info("Nenhum laboratório cadastrado.")

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

def adicionar_novo_laboratorio():
    with st.expander("Adicionar Novo Laboratório", expanded=True):
        with st.form(key='add_lab_form'):
            import re  # Import necessário para manipulação de strings
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome do Laboratório", help="Digite o nome do laboratório")
            with col2:
                capacidade = st.number_input("Capacidade", min_value=0, step=1, help="Capacidade máxima do laboratório")
            descricao = st.text_area("Descrição", help="Descrição opcional do laboratório")
            # Selecionar um administrador
            try:
                response_admins = supabase.table('users').select('id','name', 'email').eq('tipo_usuario', 'admlab').execute()
                admin_options = {admin['name'] or admin['email']: admin['id'] for admin in response_admins.data} if response_admins.data else {}
            except Exception as e:
                st.error(f'Erro ao carregar administradores: {e}')

                admin_options = {}
            administrador_email = st.selectbox("Administrador do Laboratório (opcional)", options=['Não atribuído'] + list(admin_options.keys()), help="Selecione o administrador do laboratório")
            submitted = st.form_submit_button("✅ Adicionar Laboratório")
            if submitted:
                if nome.strip() == '':
                    st.warning('O nome do laboratório é obrigatório.')
                else:
                    # Normalizar o nome para comparação
                    nome_normalizado = re.sub(' +', ' ', nome.strip().lower())
                    try:
                        response = supabase.table('laboratorios').select('nome').execute()
                        nomes_existentes = [re.sub(' +', ' ', lab['nome'].strip().lower()) for lab in response.data]
                        if nome_normalizado in nomes_existentes:
                            st.warning('Já existe um laboratório com este nome. Por favor, escolha outro nome.')
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
                        st.error(f'Erro ao verificar a existência do laboratório: {e}')

def editar_laboratorio(lab):
    st.subheader(f"Editar Laboratório: {lab['nome']}")
    with st.form(key=f'edit_lab_form_{lab["id"]}'):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome do Laboratório", value=lab['nome'], help="Atualize o nome do laboratório")
        with col2:
            capacidade = st.number_input("Capacidade", min_value=0, step=1, value=lab.get('capacidade') or 0, help="Atualize a capacidade do laboratório")
        descricao = st.text_area("Descrição", value=lab.get('descricao', ''), help="Atualize a descrição do laboratório")
        # Selecionar um administrador
        try:
            response_admins = supabase.table('users').select('id', 'name', 'email').eq('tipo_usuario', 'admlab').execute()
            admin_options = {admin['name'] or admin['email']: admin['id'] for admin in response_admins.data} if response_admins.data else {}
        except Exception as e:
            st.error(f'Erro ao carregar administradores: {e}')

            admin_options = {}
        current_admin_email = 'Não atribuído'
        if lab['administrador_id']:
            try:
                response_admin = supabase.table('users').select('email').eq('id', lab['administrador_id']).execute()
                if response_admin.data:
                    current_admin_email = response_admin.data[0]['email']
            except Exception as e:
                st.error(f'Erro ao obter o administrador atual: {e}')
        admin_emails = ['Não atribuído'] + list(admin_options.keys())
        admin_index = admin_emails.index(current_admin_email) if current_admin_email in admin_emails else 0
        administrador_email = st.selectbox("Administrador do Laboratório (opcional)", options=admin_emails, index=admin_index, help="Selecione o administrador do laboratório")
        submitted = st.form_submit_button("💾 Atualizar Dados")
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

def confirmar_exclusao_laboratorio(lab_id):
    try:
        # Obter o laboratório pelo ID
        response = supabase.table('laboratorios').select('nome').eq('id', lab_id).execute()
        if not response.data:
            st.error('Laboratório não encontrado.')
            st.session_state['confirm_delete_lab_id'] = None  # Resetar o estado
            return
        lab = response.data[0]
        st.warning(f"Tem certeza que deseja excluir o laboratório **{lab['nome']}**? Esta ação não pode ser desfeita.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button('❌ Confirmar Exclusão', key=f'confirm_delete_lab_{lab_id}'):
                try:
                    response = supabase.table('laboratorios').delete().eq('id', lab_id).execute()
                    st.success('Laboratório excluído com sucesso!')
                    st.session_state['confirm_delete_lab_id'] = None  # Resetar o estado
                    st.rerun()
                except Exception as e:
                    st.error(f'Erro ao excluir o laboratório: {e}')
                    st.session_state['confirm_delete_lab_id'] = None  # Resetar o estado
        with col2:
            if st.button('Cancelar', key=f'cancel_delete_lab_{lab_id}'):
                st.session_state['confirm_delete_lab_id'] = None  # Resetar o estado
                st.rerun()
    except Exception as e:
        st.error(f'Erro ao obter o laboratório: {e}')
        st.session_state['confirm_delete_lab_id'] = None  # Resetar o estado


