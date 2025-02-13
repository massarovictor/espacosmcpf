# admlab.py
import streamlit as st
from datetime import date
from database import supabase
from email_service import send_email  # Certifique-se de importar o módulo de e-mail


def painel_admin_laboratorio():
    st.title("📅 Espaços MCPF")  # Título do sistema
    st.subheader("Painel de Administração dos Laboratórios")
    st.write("**EEEP Professora Maria Célia Pinheiro Falcão**")
   
    administrador_id = st.session_state["usuario_id"]

    try:
        # Obter laboratórios associados ao administrador
        response = supabase.table('laboratorios').select('*').eq('administrador_id', administrador_id).execute()
        laboratorios = response.data

        if not laboratorios:
            st.info('Você não está associado a nenhum laboratório.')
            return

        for lab in laboratorios:
            st.subheader(f"Laboratório de {lab['nome']}")

            tab1, tab2, tab3 = st.tabs(["Agendamentos Pendentes", "Horários Fixos", "Histórico de Atividades"])

            with tab1:
                gerenciar_agendamentos_pendentes(lab['id'])

            with tab2:
                gerenciar_horarios_fixos(lab['id'])
            
            with tab3:
                visualizar_historico_atividades(lab['id'])

    except Exception as e:
        st.error(f'Erro ao carregar os laboratórios: {e}')


import streamlit as st
from datetime import date
from database import supabase

def visualizar_historico_atividades(laboratorio_id):
    st.subheader("📜 Histórico de Atividades")

    try:
        # Buscar todos os agendamentos passados para este laboratório
        hoje = date.today().isoformat()  # Data de hoje para comparação
        response_agendamentos = (
            supabase.table('agendamentos')
            .select('id', 'usuario_id', 'data_agendamento', 'aulas', 'descricao', 'status')
            .eq('laboratorio_id', laboratorio_id)
            .lt('data_agendamento', hoje)  # Apenas agendamentos passados
            .execute()
        )
        agendamentos = response_agendamentos.data

        if not agendamentos:
            st.info('Nenhuma atividade passada registrada neste espaço.')
            return

        # Criar uma lista formatada para exibição
        historico = []
        for agendamento in agendamentos:
            # Buscar nome do professor
            response_user = supabase.table('users').select('name').eq('id', agendamento['usuario_id']).execute()
            nome_professor = response_user.data[0]['name'] if response_user.data else "Desconhecido"

            # Formatar a lista de aulas
            aulas = ', '.join([f"{aula}ª Aula" for aula in sorted(agendamento['aulas'])])

            historico.append({
                "Professor(a)": nome_professor,
                "Data": agendamento['data_agendamento'],
                "Aulas": aulas,
                "Descrição": agendamento['descricao'],
                "Status": agendamento['status'].capitalize()
            })

        # Criar um container para alinhar com os demais elementos da interface
        with st.container():
            st.write("📌 **Lista de atividades já realizadas:**")
            
            # Exibir a tabela com layout responsivo ocupando toda a largura disponível
            st.dataframe(
                historico,
                use_container_width=True  # Expande a tabela para ocupar toda a largura disponível
            )

    except Exception as e:
        st.error(f'Erro ao carregar o histórico de atividades: {e}')

def gerenciar_agendamentos_pendentes(laboratorio_id):
    st.subheader("Agendamentos Pendentes")
    try:
        # Obter agendamentos pendentes para este laboratório
        response_agendamentos = supabase.table('agendamentos').select('*').eq('laboratorio_id', laboratorio_id).eq('status', 'pendente').execute()
        agendamentos = response_agendamentos.data
        if not agendamentos:
            st.info('Nenhum agendamento pendente.')
        else:
            for agendamento in agendamentos:
                exibir_agendamento_para_validacao(agendamento)
    except Exception as e:
        st.error(f'Erro ao carregar os agendamentos: {e}')

def exibir_agendamento_para_validacao(agendamento):
    try:
        # Obter informações adicionais
        # Obter nome do professor
        response_user = supabase.table('users').select('name').eq('id', agendamento['usuario_id']).execute()
        professor_name = response_user.data[0]['name'] if response_user.data else 'Desconhecido'

        aulas = [f"{aula}ª Aula" for aula in agendamento['aulas']]
        st.write(f"**Professor:** {professor_name}")
        st.write(f"**Data:** {agendamento['data_agendamento']}")

        st.write(f"**Aulas:** {', '.join(aulas)}")
        st.write(f"**Status:** {agendamento['status']}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Aprovar", key=f"aprovar_{agendamento['id']}"):
                atualizar_status_agendamento(agendamento['id'], 'aprovado')
        with col2:
            if st.button("❌ Rejeitar", key=f"rejeitar_{agendamento['id']}"):
                atualizar_status_agendamento(agendamento['id'], 'rejeitado')
    except Exception as e:
        st.error(f'Erro ao exibir agendamento: {e}')

def atualizar_status_agendamento(agendamento_id, novo_status):
    try:
        # Atualiza o status do agendamento no banco de dados
        response = supabase.table('agendamentos').update({'status': novo_status}).eq('id', agendamento_id).execute()
        st.success(f'Agendamento {novo_status} com sucesso!')
        
        # Recupera os detalhes do agendamento para montar a notificação
        response_agendamento = supabase.table('agendamentos').select('usuario_id', 'laboratorio_id', 'data_agendamento', 'descricao').eq('id', agendamento_id).execute()
        if response_agendamento.data:
            agendamento_info = response_agendamento.data[0]
            usuario_id = agendamento_info['usuario_id']
            # Recupera o e-mail do professor
            response_user = supabase.table('users').select('email').eq('id', usuario_id).execute()
            email_usuario = response_user.data[0]['email'] if response_user.data else None
            
            if email_usuario:
                subject = f"Agendamento {novo_status.capitalize()}"
                body = (
                    f"Olá,\n\n"
                    f"Informamos que o seu agendamento para o espaço {nome_laboratorio}, marcado para o dia {data_agendamento}, foi {novo_status}.\n\n"
                    f"Descrição da atividade: {agendamento_info.get('descricao', 'Sem descrição')}\n\n"
                    "Caso necessite de esclarecimentos adicionais ou tenha dúvidas, por favor, entre em contato conosco.\n\n"
                    "Atenciosamente,\nEquipe 🦉AgendaMCPF"
                )

                send_email(subject, body, email_usuario)
        st.rerun()
    except Exception as e:
        st.error(f'Erro ao atualizar o status do agendamento: {e}')

def gerenciar_horarios_fixos(laboratorio_id):
    st.subheader("Gerenciar Horários Fixos")
    # Mapeamento inverso para exibir o nome do dia da semana
    dias_semana_inverso = {
        0: 'Segunda',
        1: 'Terça',
        2: 'Quarta',
        3: 'Quinta',
        4: 'Sexta'
    }
    # Exibir horários fixos existentes
    try:
        response_horarios = supabase.table('horarios_fixos').select('*').eq('laboratorio_id', laboratorio_id).execute()
        horarios = response_horarios.data

        if horarios:
            # Ordenar os horários por dia da semana
            horarios.sort(key=lambda x: x['dia_semana'])
            for horario in horarios:
                dia_semana_nome = dias_semana_inverso.get(horario['dia_semana'], 'Desconhecido')
                aulas_formatadas = ', '.join([f'{aula}ª Aula' for aula in sorted(horario['aulas'])])
                periodo = f"{horario['data_inicio']} até {horario['data_fim']}"
                with st.expander(f"{dia_semana_nome} - {aulas_formatadas}"):
                    st.write(f"**Período:** {periodo}")
                    st.write(f"**Descrição:** {horario.get('descricao', '')}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📝 Editar Horário", key=f"editar_horario_{horario['id']}"):
                            editar_horario_fixo(horario)
                    with col2:
                        if st.button("❌ Excluir Horário", key=f"excluir_horario_{horario['id']}"):
                            remover_horario_fixo(horario['id'])
        else:
            st.info("Nenhum horário fixo cadastrado.")

    except Exception as e:
        st.error(f'Erro ao carregar os horários fixos: {e}')

    st.markdown("---")
    st.subheader("Adicionar Novo Horário Fixo")
    adicionar_horario_fixo(laboratorio_id)

def adicionar_horario_fixo(laboratorio_id):
    with st.form(key='form_adicionar_horario_fixo'):
        # Mapeamento dos dias da semana para inteiros
        dias_semana_opcoes = {
            'Segunda': 0,
            'Terça': 1,
            'Quarta': 2,
            'Quinta': 3,
            'Sexta': 4
        }

        dia_semana_nome = st.selectbox("Dia da Semana", options=list(dias_semana_opcoes.keys()))
        dia_semana = dias_semana_opcoes[dia_semana_nome]  # Obter o valor inteiro correspondente
        aulas_selecionadas = st.multiselect("Selecione as Aulas", options=list(range(1, 10)))  # Aulas de 1 a 9
        data_inicio = st.date_input("Data de Início", value=date.today())
        data_fim = st.date_input("Data de Fim", value=date.today())
        descricao = st.text_input("Descrição (opcional)")
        submitted = st.form_submit_button("✅ Adicionar Horário Fixo")
        if submitted:
            if not aulas_selecionadas:
                st.warning("Por favor, selecione ao menos uma aula.")
            elif data_inicio > data_fim:
                st.warning("A data de início não pode ser posterior à data de fim.")
            else:
                novo_horario = {
                    'laboratorio_id': laboratorio_id,
                    'dia_semana': dia_semana,  # Agora é um inteiro
                    'aulas': aulas_selecionadas,
                    'data_inicio': data_inicio.isoformat(),
                    'data_fim': data_fim.isoformat(),
                    'descricao': descricao.strip()
                }
                try:
                    response = supabase.table('horarios_fixos').insert(novo_horario).execute()
                    st.success("Horário fixo adicionado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f'Erro ao adicionar o horário fixo: {e}')

def editar_horario_fixo(horario):
    st.subheader(f"Editar Horário Fixo - ID {horario['id']}")
    with st.form(key=f'form_editar_horario_fixo_{horario["id"]}'):
        dias_semana_opcoes = {
            'Segunda': 0,
            'Terça': 1,
            'Quarta': 2,
            'Quinta': 3,
            'Sexta': 4
        }
        dias_semana_inverso = {v: k for k, v in dias_semana_opcoes.items()}

        dia_semana_nome = st.selectbox("Dia da Semana", options=list(dias_semana_opcoes.keys()), index=horario['dia_semana'])
        dia_semana = dias_semana_opcoes[dia_semana_nome]
        aulas_selecionadas = st.multiselect("Selecione as Aulas", options=list(range(1, 10)), default=horario['aulas'])
        data_inicio = st.date_input("Data de Início", value=date.fromisoformat(horario['data_inicio']))
        data_fim = st.date_input("Data de Fim", value=date.fromisoformat(horario['data_fim']))
        descricao = st.text_input("Descrição (opcional)", value=horario.get('descricao', ''))

        submitted = st.form_submit_button("💾 Atualizar Horário Fixo")
        if submitted:
            if not aulas_selecionadas:
                st.warning("Por favor, selecione ao menos uma aula.")
            elif data_inicio > data_fim:
                st.warning("A data de início não pode ser posterior à data de fim.")
            else:
                horario_atualizado = {
                    'dia_semana': dia_semana,
                    'aulas': aulas_selecionadas,
                    'data_inicio': data_inicio.isoformat(),
                    'data_fim': data_fim.isoformat(),
                    'descricao': descricao.strip()
                }
                try:
                    response = supabase.table('horarios_fixos').update(horario_atualizado).eq('id', horario['id']).execute()
                    st.success("Horário fixo atualizado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f'Erro ao atualizar o horário fixo: {e}')

def remover_horario_fixo(horario_id):
    try:
        response = supabase.table('horarios_fixos').delete().eq('id', horario_id).execute()
        st.success("Horário fixo excluído com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f'Erro ao remover o horário fixo: {e}')
