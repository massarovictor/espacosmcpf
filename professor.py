import streamlit as st
from database import supabase
from datetime import date, datetime, timedelta
import pandas as pd

def painel_professor():
    st.title("📅 Espaços MCPF")  # Título do sistema
    st.subheader("Painel de Administração do Professor")
    st.write("**EEEP Professora Maria Célia Pinheiro Falcão**")
    st.markdown("---")  # Linha separadora para organizar o layout

    tab1, tab2, tab3 = st.tabs(["Agendar Laboratório", "Meus Agendamentos", "Agenda do Laboratório"])

    with tab1:
        agendar_laboratorio()

    with tab2:
        listar_agendamentos_professor()

    with tab3:
        visualizar_agenda_laboratorio()

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

        data_agendamento = st.date_input("Data do Agendamento", min_value=date.today())
        aulas_opcoes = list(range(1, 10))  # Aulas de 1 a 9
        aulas_selecionadas = st.multiselect("Selecione a(s) aula(s) para agendamento", aulas_opcoes)

        # Campo para descrição da atividade
        descricao = st.text_input("Descrição da Atividade", help="Insira uma breve descrição da atividade a ser realizada")

        if st.button("Confirmar Agendamento"):
            if len(aulas_selecionadas) < 1:
                st.warning("Por favor, selecione pelo menos uma aula para agendamento.")
            elif descricao.strip() == '':
                st.warning("Por favor, coloque uma descrição da atividade a ser feita no laboratório.")
            else:
                conflito, aulas_conflito = verificar_disponibilidade(laboratorio_id, data_agendamento, aulas_selecionadas)
                if not conflito:
                    confirmar_agendamento_professor(laboratorio_id, data_agendamento, aulas_selecionadas, descricao)
                else:
                    aulas_conflito_str = ', '.join([f"{aula}ª Aula" for aula in aulas_conflito])
                    st.error(f'O laboratório não está disponível nas seguintes aulas: {aulas_conflito_str}')
    except Exception as e:
        st.error(f'Erro ao agendar laboratório: {e}')

def verificar_disponibilidade(laboratorio_id, data_agendamento, aulas_numeros):
    try:
        aulas_indisponiveis = set()
        dia_semana = data_agendamento.weekday()  # 0 (Segunda-feira) a 6 (Domingo)
        response_horarios_fixos = supabase.table('horarios_fixos').select('*').eq('laboratorio_id', laboratorio_id).eq('dia_semana', dia_semana).execute()
        horarios_fixos = response_horarios_fixos.data
        for horario_fixo in horarios_fixos:
            data_inicio = datetime.strptime(horario_fixo['data_inicio'], '%Y-%m-%d').date()
            data_fim = datetime.strptime(horario_fixo['data_fim'], '%Y-%m-%d').date()
            if data_inicio <= data_agendamento <= data_fim:
                aulas_fixas = horario_fixo['aulas']
                aulas_indisponiveis.update(aulas_fixas)

        response_agendamentos = supabase.table('agendamentos').select('*').eq('laboratorio_id', laboratorio_id).eq('data_agendamento', data_agendamento.isoformat()).eq('status', 'aprovado').execute()
        agendamentos_existentes = response_agendamentos.data
        for agendamento in agendamentos_existentes:
            aulas_agendadas = agendamento['aulas']
            aulas_indisponiveis.update(aulas_agendadas)

        conflito = set(aulas_numeros) & aulas_indisponiveis
        if conflito:
            return True, conflito
        else:
            return False, None
    except Exception as e:
        st.error(f'Erro ao verificar disponibilidade: {e}')
        return True, None

def verificar_duplo_agendamento(usuario_id,laboratorio_id, data_agendamento, aulas_selecionadas):
    aulas_selecionadas_pg = '{' + ','.join(map(str, aulas_selecionadas)) + '}' # convertendo [] para {} para a requisição no PostGres
    try:
        ocorrencia = supabase.table('agendamentos').select('*').eq('usuario_id', usuario_id).eq('laboratorio_id', laboratorio_id).eq('data_agendamento', data_agendamento.isoformat()).eq('aulas', aulas_selecionadas_pg).eq('status', 'pendente').execute()
        # essa ocorrencia se refere a ocorrencia de algum registro igual e pendente no banco de dados, que caso seja encontrado, retorna um erro.
        if (ocorrencia.data):
            return 0
        else:
            return 1 # se não encontrar registro, retorna 1, para dizer que o programa pode prosseguir
    except Exception as e:
        st.error(e)
    

def confirmar_agendamento_professor(laboratorio_id, data_agendamento, aulas_selecionadas, descricao):
    usuario_id = st.session_state["usuario_id"]
    novo_agendamento = {
        'usuario_id': usuario_id,
        'laboratorio_id': laboratorio_id,
        'data_agendamento': data_agendamento.isoformat(),
        'aulas': aulas_selecionadas,
        'descricao': descricao,
        'status': 'pendente'
    }
    verificacao = verificar_duplo_agendamento(usuario_id,laboratorio_id, data_agendamento, aulas_selecionadas)
    if (verificacao == 1):
        try:
            response = supabase.table('agendamentos').insert(novo_agendamento).execute()
            st.success('Agendamento solicitado com sucesso! Aguardando aprovação.')
        except Exception as e:
            st.error(f'Erro ao salvar o agendamento: {e}')
    else:
        st.error("Você já requisitou esse agendamento. Espere a revisão do administrador")

def listar_agendamentos_professor():
    st.subheader("Meus Agendamentos")
    usuario_id = st.session_state["usuario_id"]
    try:
        response = supabase.table('agendamentos').select('*').eq('usuario_id', usuario_id).order('data_agendamento', desc=False).execute()
        agendamentos = response.data
        if not agendamentos:
            st.info('Você não possui agendamentos.')
        else:
            for agendamento in agendamentos:
                response_lab = supabase.table('laboratorios').select('nome').eq('id', agendamento['laboratorio_id']).execute()
                lab_nome = response_lab.data[0]['nome'] if response_lab.data else 'Desconhecido'
                aulas = [f"{aula}ª Aula" for aula in sorted(agendamento['aulas'])]
                descricao = agendamento.get('descricao', 'Sem descrição')
                st.write(f"📅 **Data:** {agendamento['data_agendamento']} | **Laboratório:** {lab_nome} | **Aulas:** {', '.join(aulas)} | **Status:** {agendamento['status']} | **Descrição:** {descricao}")
    except Exception as e:
        st.error(f'Erro ao carregar seus agendamentos: {e}')

def visualizar_agenda_laboratorio():
    st.subheader("Agenda do Laboratório")
    try:
        response_labs = supabase.table('laboratorios').select('id', 'nome').execute()
        laboratorios = response_labs.data
        if not laboratorios:
            st.error('Nenhum laboratório disponível.')
            return
        lab_options = {lab['nome']: lab['id'] for lab in laboratorios}
        lab_nome = st.selectbox("Escolha o Laboratório", options=list(lab_options.keys()), key="lab_select_agenda")
        laboratorio_id = lab_options[lab_nome]

        data_inicio = st.date_input("Data Início", value=date.today())
        data_fim = st.date_input("Data Fim", value=date.today() + timedelta(days=7))

        if data_inicio > data_fim:
            st.warning("A data de início não pode ser posterior à data de fim.")
            return

        if st.button("Consultar Agenda"):
            delta = data_fim - data_inicio
            datas = [data_inicio + timedelta(days=i) for i in range(delta.days + 1)]

            agenda = {}
            for data in datas:
                agenda[data] = {'Horários Fixos': [], 'Agendamentos': []}

            response_horarios_fixos = supabase.table('horarios_fixos').select('*').eq('laboratorio_id', laboratorio_id).execute()
            horarios_fixos = response_horarios_fixos.data
            for horario in horarios_fixos:
                data_inicio_fixo = datetime.strptime(horario['data_inicio'], '%Y-%m-%d').date()
                data_fim_fixo = datetime.strptime(horario['data_fim'], '%Y-%m-%d').date()
                for data in datas:
                    if data_inicio_fixo <= data <= data_fim_fixo:
                        dia_semana = data.weekday()
                        if dia_semana == horario['dia_semana']:
                            aulas = ', '.join([f"{aula}ª Aula" for aula in sorted(horario['aulas'])])
                            agenda[data]['Horários Fixos'].append({'Aulas': aulas, 'Descrição': horario.get('descricao', '')})

            response_agendamentos = supabase.table('agendamentos').select('*').eq('laboratorio_id', laboratorio_id).gte('data_agendamento', data_inicio.isoformat()).lte('data_agendamento', data_fim.isoformat()).eq('status', 'aprovado').execute()
            agendamentos = response_agendamentos.data
            for agendamento in agendamentos:
                data_ag = datetime.strptime(agendamento['data_agendamento'], '%Y-%m-%d').date()
                aulas = ', '.join([f"{aula}ª Aula" for aula in sorted(agendamento['aulas'])])
                response_user = supabase.table('users').select('email').eq('id', agendamento['usuario_id']).execute()
                professor_email = response_user.data[0]['email'] if response_user.data else 'Desconhecido'
                agenda[data_ag]['Agendamentos'].append({'Aulas': aulas, 'Professor': professor_email, 'Descrição': agendamento.get('descricao', '')})

            for data in datas:
                st.write(f"### 📅 {data.strftime('%d/%m/%Y')}")
                if agenda[data]['Horários Fixos']:
                    st.write("**Horários Fixos:**")
                    st.table(pd.DataFrame(agenda[data]['Horários Fixos']))
                if agenda[data]['Agendamentos']:
                    st.write("**Agendamentos Aprovados:**")
                    st.table(pd.DataFrame(agenda[data]['Agendamentos']))
                if not agenda[data]['Horários Fixos'] and not agenda[data]['Agendamentos']:
                    st.write("Não há horários fixos ou agendamentos para esta data.")
                st.markdown("---")
    except Exception as e:
        st.error(f'Erro ao carregar a agenda do laboratório: {e}')
