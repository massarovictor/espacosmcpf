import streamlit as st
import bcrypt
from database import supabase


def adicionar_usuario():
    with st.expander("Adicionar Novo Usuário", expanded=True):
        with st.form(key='add_user_form'):
            novo_nome = st.text_input("Nome", help="Digite o nome do usuário")
            col1, col2 = st.columns(2)
            with col1:
                novo_email = st.text_input("Email", help="Digite um e-mail válido")
            with col2:
                novo_tipo = st.radio("Tipo de Usuário", options=['admlab', 'professor'], help="Selecione o tipo de usuário")
            col3, col4 = st.columns(2)
            with col3:
                nova_senha = st.text_input("Senha", type='password', help="Digite uma senha segura")
            with col4:
                senha_confirmacao = st.text_input("Confirme a Senha", type='password', help="Confirme a senha")

            submitted = st.form_submit_button("✅ Adicionar Usuário")
            if submitted:
                if nova_senha != senha_confirmacao:
                    st.warning('As senhas não coincidem.')
                elif novo_email.strip() == '' or nova_senha.strip() == '':
                    st.warning('Email e senha são obrigatórios.')
                else:
                    # Hash da senha
                    hashed_password = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    novo_usuario = {
                        'name': novo_nome.strip(),
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

def editar_usuario(usuario):
    st.subheader(f"Editar Usuário: {usuario['email']}")
    with st.form(key=f"edit_user_{usuario['id']}"):
        novo_nome = st.text_input("Nome", value=usuario['name'], help="Atualize o nome do usuário")
        col1, col2 = st.columns(2)
        with col1:

            novo_email = st.text_input("Email", value=usuario['email'], help="Atualize o email do usuário")
        with col2:
            novo_tipo = st.radio("Tipo de Usuário", options=['admlab', 'professor'], index=['admlab', 'professor'].index(usuario['tipo_usuario']), help="Selecione o novo tipo de usuário")
        col3, col4 = st.columns(2)
        with col3:
            nova_senha = st.text_input("Nova Senha (deixe em branco para não alterar)", type='password', help="Digite uma nova senha")
        with col4:
            senha_confirmacao = st.text_input("Confirme a Nova Senha", type='password', help="Confirme a nova senha")

        submitted = st.form_submit_button("💾 Atualizar Dados")

        if submitted:
            st.write(novo_email)
            if nova_senha != senha_confirmacao:
                st.warning('As senhas não coincidem.')

            elif novo_email.strip() == '':
                st.warning('O email não pode estar vazio.')
            else:
                update_data = {
                    'name': novo_nome.strip(),
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



def confirmar_exclusao_usuario(usuario_id):
    try:
        # Obter o usuário pelo ID
        response = supabase.table('users').select('email').eq('id', usuario_id).execute()
        if not response.data:
            st.error('Usuário não encontrado.')
            st.session_state['confirm_delete_user_id'] = None  # Resetar o estado
            return
        usuario = response.data[0]
        st.warning(f"Tem certeza que deseja excluir o usuário **{usuario['email']}**? Esta ação não pode ser desfeita.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button('❌ Confirmar Exclusão', key=f'confirm_delete_user_{usuario_id}'):
                try:
                    response = supabase.table('users').delete().eq('id', usuario_id).execute()
                    st.success('Usuário excluído com sucesso!')
                    st.session_state['confirm_delete_user_id'] = None  # Resetar o estado
                    st.rerun()
                except Exception as e:
                    st.error(f'Erro ao excluir o usuário: {e}')
                    st.session_state['confirm_delete_user_id'] = None  # Resetar o estado
        with col2:
            if st.button('Cancelar', key=f'cancel_delete_user_{usuario_id}'):
                st.session_state['confirm_delete_user_id'] = None  # Resetar o estado
                st.rerun()
    except Exception as e:
        st.error(f'Erro ao obter o usuário: {e}')
        st.session_state['confirm_delete_user_id'] = None  # Resetar o estado

def ler_usuario(usuario_id):
    # Lógica para ler um usuário
    pass

def atualizar_usuario(usuario_id, novos_dados):
    # Lógica para atualizar um usuário
    pass

def deletar_usuario(usuario_id):
    # Lógica para deletar um usuário
    pass

def criar_laboratorio(laboratorio):
    # Lógica para criar um laboratório
    pass

def ler_laboratorio(laboratorio_id):
    # Lógica para ler um laboratório
    pass

def atualizar_laboratorio(laboratorio_id, novos_dados):
    # Lógica para atualizar um laboratório
    pass

def deletar_laboratorio(laboratorio_id):
    # Lógica para deletar um laboratório
    pass