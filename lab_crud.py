import streamlit as st
import re
from database import supabase

def adicionar_novo_laboratorio():
    with st.expander("Adicionar Novo Espaço", expanded=True):
        with st.form(key='add_lab_form'):
            import re  # Import necessário para manipulação de strings
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome do Espaço", help="Digite o nome do Espaço")
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
            administrador_email = st.selectbox("Administrador do Espaço (opcional)", options=['Não atribuído'] + list(admin_options.keys()), help="Selecione o administrador do Espaço")
            submitted = st.form_submit_button("✅ Adicionar Laboratório")
            if submitted:
                if nome.strip() == '':
                    st.warning('O nome do Espaço é obrigatório.')
                else:
                    # Normalizar o nome para comparação
                    nome_normalizado = re.sub(' +', ' ', nome.strip().lower())
                    try:
                        response = supabase.table('laboratorios').select('nome').execute()
                        nomes_existentes = [re.sub(' +', ' ', lab['nome'].strip().lower()) for lab in response.data]
                        if nome_normalizado in nomes_existentes:
                            st.warning('Já existe um Espaço com este nome. Por favor, escolha outro nome.')
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
                                st.success('Espaço adicionado com sucesso!')
                                st.rerun()
                            except Exception as e:
                                st.error(f'Erro ao adicionar o Espaço: {e}')
                    except Exception as e:
                        st.error(f'Erro ao verificar a existência do Espaço: {e}')

def editar_laboratorio(lab):
    st.subheader(f"Editar Espaço: {lab['nome']}")
    with st.form(key=f'edit_lab_form_{lab["id"]}'):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome do Espaço", value=lab['nome'], help="Atualize o nome do laboratório")
        with col2:
            capacidade = st.number_input("Capacidade", min_value=0, step=1, value=lab.get('capacidade') or 0, help="Atualize a capacidade do laboratório")
        descricao = st.text_area("Descrição", value=lab.get('descricao', ''), help="Atualize a descrição do Espaço")
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
        administrador_email = st.selectbox("Administrador do Espaço (opcional)", options=admin_emails, index=admin_index, help="Selecione o administrador do Espaço")
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
                    st.success('Espaço atualizado com sucesso!')
                    st.rerun()
                except Exception as e:
                    st.error(f'Erro ao atualizar o Espaço: {e}')



def confirmar_exclusao_laboratorio(lab_id):
    try:
        # Obter o laboratório pelo ID
        response = supabase.table('laboratorios').select('nome').eq('id', lab_id).execute()
        if not response.data:
            st.error('Espaço não encontrado.')
            st.session_state['confirm_delete_lab_id'] = None  # Resetar o estado
            return
        lab = response.data[0]
        st.warning(f"Tem certeza que deseja excluir o Espaço **{lab['nome']}**? Esta ação não pode ser desfeita.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button('❌ Confirmar Exclusão', key=f'confirm_delete_lab_{lab_id}'):
                try:
                    response = supabase.table('laboratorios').delete().eq('id', lab_id).execute()
                    st.success('Espaço excluído com sucesso!')
                    st.session_state['confirm_delete_lab_id'] = None  # Resetar o estado
                    st.rerun()
                except Exception as e:
                    st.error(f'Erro ao excluir o Espaço: {e}')
                    st.session_state['confirm_delete_lab_id'] = None  # Resetar o estado
        with col2:
            if st.button('Cancelar', key=f'cancel_delete_lab_{lab_id}'):
                st.session_state['confirm_delete_lab_id'] = None  # Resetar o estado
                st.rerun()
    except Exception as e:
        st.error(f'Erro ao obter o Espaço: {e}')
        st.session_state['confirm_delete_lab_id'] = None  # Resetar o estado



def confirmar_exclusao_laboratorio(lab_id):
    try:
        # Obter o laboratório pelo ID
        response = supabase.table('laboratorios').select('nome').eq('id', lab_id).execute()
        if not response.data:
            st.error('Espaço não encontrado.')
            st.session_state['confirm_delete_lab_id'] = None  # Resetar o estado
            return
        lab = response.data[0]
        st.warning(f"Tem certeza que deseja excluir o Espaço **{lab['nome']}**? Esta ação não pode ser desfeita.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button('❌ Confirmar Exclusão', key=f'confirm_delete_lab_{lab_id}'):
                try:
                    response = supabase.table('laboratorios').delete().eq('id', lab_id).execute()
                    st.success('Espaço excluído com sucesso!')
                    st.session_state['confirm_delete_lab_id'] = None  # Resetar o estado
                    st.rerun()
                except Exception as e:
                    st.error(f'Erro ao excluir o espaço: {e}')
                    st.session_state['confirm_delete_lab_id'] = None  # Resetar o estado
        with col2:
            if st.button('Cancelar', key=f'cancel_delete_lab_{lab_id}'):
                st.session_state['confirm_delete_lab_id'] = None  # Resetar o estado
                st.rerun()
    except Exception as e:
        st.error(f'Erro ao obter o espaço: {e}')
        st.session_state['confirm_delete_lab_id'] = None  # Resetar o estado
