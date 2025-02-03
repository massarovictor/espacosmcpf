import streamlit as st
from datetime import date, datetime, timedelta
import pandas as pd
from database import supabase

def painel_professor():
    """
    Painel do Professor:
    - Sem botão de Refresh.
    - Botão de Logout ao final.
    - 3 abas:
      1) Agendar Espaço (formulário)
      2) Meus Agendamentos (DataFrame)
      3) Agenda do Espaço (DataFrame)
    """
    # Cabeçalho principal
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

    # Abas principais
    tab1, tab2, tab3 = st.tabs(["Agendar Espaço", "Meus Agendamentos", "Agenda do Espaço"])

    with tab1:
        agendar_laboratorio()

    with tab2:
        listar_agendamentos_professor()

    with tab3:
        visualizar_agenda_laboratorio()

    st.markdown("---")
    # Botão de Logout no final
    if st.button("Logout"):
        efetuar_logout()

# =============================================================================
#                           1) AGENDAR ESPAÇO
# =============================================================================

def agendar_laboratorio():
    """
    Formulário simples para agendar o laboratório:
    - Escolher lab
    - Data
    - Aulas
    - Descrição
    Verifica disponibilidade e cria agendamento pendente.
    """
    st.subheader("Agendar um Laboratório")

    try:
        labs = supabase.table('laboratorios').select('id, nome').execute().data or []
        if not labs:
            st.error("Nenhum laboratório disponível.")
            return

        # Mapeando {nome_do_lab -> id_do_lab}
        lab_map = {lb['nome']: lb['id'] for lb in labs}

        with st.form(key="form_agendar_lab"):
            lab_nome = st.selectbox("Escolha o Laboratório", options=list(lab_map.keys()))
            laboratorio_id = lab_map[lab_nome]

            data_agendamento = st.date_input("Data do Agendamento", min_value=date.today())
            aulas_opcoes = list(range(1, 10))
            aulas_selecionadas = st.multiselect("Selecione a(s) aula(s)", aulas_opcoes)
            descricao = st.text_input("Descrição da Atividade", help="Breve descrição da atividade")

            submitted = st.form_submit_button("Confirmar Agendamento")
            if submitted:
                if not aulas_selecionadas:
                    st.warning("Por favor, selecione pelo menos uma aula.")
                elif not descricao.strip():
                    st.warning("Por favor, informe uma descrição da atividade.")
                else:
                    conflito, aulas_conf = verificar_disponibilidade(laboratorio_id, data_agendamento, aulas_selecionadas)
                    if conflito:
                        confl_str = ", ".join([f"{a}ª Aula" for a in aulas_conf])
                        st.error(f"O laboratório não está disponível nas aulas: {confl_str}")
                    else:
                        confirmar_agendamento_professor(laboratorio_id, data_agendamento, aulas_selecionadas, descricao)

    except Exception as e:
        st.error(f"Erro ao agendar laboratório: {e}")

# =============================================================================
#              2) MEUS AGENDAMENTOS (DataFrame)
# =============================================================================

def listar_agendamentos_professor():
    """
    Exibe todos os agendamentos do professor em DataFrame,
    ordenados localmente por data_agendamento.
    """
    st.subheader("Meus Agendamentos")

    usuario_id = st.session_state.get("usuario_id")
    if not usuario_id:
        st.error("Usuário não autenticado. Faça login novamente.")
        return

    try:
        resp = supabase.table('agendamentos').select('*').eq('usuario_id', usuario_id).execute()
        agendamentos = resp.data or []

        if not agendamentos:
            st.info("Você não possui agendamentos.")
            return

        # Ordenar localmente por data_agendamento
        agendamentos.sort(key=lambda x: x['data_agendamento'])

        linhas = []
        for ag in agendamentos:
            # Buscar nome do laboratório
            lab_resp = supabase.table('laboratorios').select('nome').eq('id', ag['laboratorio_id']).execute().data or []
            lab_nome = lab_resp[0]['nome'] if lab_resp else "Desconhecido"

            aulas_str = ", ".join([f"{a}ª Aula" for a in sorted(ag['aulas'])])
            desc = ag.get('descricao',"Sem descrição")
            linhas.append({
                "Data": ag['data_agendamento'],
                "Laboratório": lab_nome,
                "Aulas": aulas_str,
                "Status": ag['status'],
                "Descrição": desc
            })

        df = pd.DataFrame(linhas)
        st.dataframe(
            df,
            column_config={
                "Data": "Data do Agendamento",
                "Laboratório": "Laboratório",
                "Aulas": "Aulas",
                "Status": "Status",
                "Descrição": "Descrição",
            },
            hide_index=True,
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Erro ao carregar seus agendamentos: {e}")

# =============================================================================
#         3) AGENDA DO LABORATÓRIO (DataFrame)
# =============================================================================

def visualizar_agenda_laboratorio():
    """
    Exibe a agenda (horários fixos + agendamentos aprovados) em DataFrame,
    num intervalo [data_inicio, data_fim].
    """
    st.subheader("Agenda do Laboratório")

    try:
        labs = supabase.table('laboratorios').select('id, nome').execute().data or []
        if not labs:
            st.error("Nenhum laboratório disponível.")
            return

        lab_map = {lb['nome']: lb['id'] for lb in labs}
        lab_nome = st.selectbox("Escolha o Laboratório", options=list(lab_map.keys()), key="lab_select_prof_agenda")
        laboratorio_id = lab_map[lab_nome]

        dt_i = st.date_input("Data Início", value=date.today())
        dt_f = st.date_input("Data Fim", value=date.today() + timedelta(days=7))

        if dt_i > dt_f:
            st.warning("A data de início não pode ser posterior à data de fim.")
            return

        if st.button("Consultar Agenda"):
            agenda_df = montar_agenda_df(laboratorio_id, dt_i, dt_f)
            if agenda_df.empty:
                st.info("Nenhum horário fixo ou agendamento aprovado nesse intervalo.")
            else:
                st.dataframe(
                    agenda_df,
                    column_config={
                        "Data": "Data",
                        "Tipo": "Tipo (Fixo/Aprov.)",
                        "Aulas": "Aulas",
                        "Professor": "Professor",
                        "Descrição": "Descrição",
                    },
                    hide_index=True,
                    use_container_width=True
                )
    except Exception as e:
        st.error(f"Erro ao carregar a agenda: {e}")

def montar_agenda_df(laboratorio_id, dt_i, dt_f):
    datas = [dt_i + timedelta(days=i) for i in range((dt_f - dt_i).days+1)]

    # Horários fixos
    hf = supabase.table('horarios_fixos').select('*') \
        .eq('laboratorio_id', laboratorio_id).execute().data or []
    # Agendamentos aprovados
    ag = supabase.table('agendamentos').select('*') \
        .eq('laboratorio_id', laboratorio_id) \
        .eq('status','aprovado') \
        .gte('data_agendamento', dt_i.isoformat()) \
        .lte('data_agendamento', dt_f.isoformat()) \
        .execute().data or []

    linhas = []
    # Processar horários fixos
    for h in hf:
        d_i = datetime.strptime(h['data_inicio'], "%Y-%m-%d").date()
        d_f = datetime.strptime(h['data_fim'], "%Y-%m-%d").date()
        for d in datas:
            if d_i <= d <= d_f and d.weekday() == h['dia_semana']:
                aulas_str = ", ".join([f"{x}ª Aula" for x in sorted(h['aulas'])])
                linhas.append({
                    "Data": d.strftime("%Y-%m-%d"),
                    "Tipo": "Fixo",
                    "Aulas": aulas_str,
                    "Professor": "",
                    "Descrição": h.get("descricao","")
                })

    # Processar agendamentos aprovados
    for a in ag:
        d_ag = datetime.strptime(a['data_agendamento'], "%Y-%m-%d").date()
        if dt_i <= d_ag <= dt_f:
            aulas_str = ", ".join([f"{x}ª Aula" for x in sorted(a['aulas'])])
            user = supabase.table('users').select('email').eq('id', a['usuario_id']).execute().data or []
            prof_email = user[0]['email'] if user else "Desconhecido"
            linhas.append({
                "Data": d_ag.strftime("%Y-%m-%d"),
                "Tipo": "Aprovado",
                "Aulas": aulas_str,
                "Professor": prof_email,
                "Descrição": a.get("descricao","")
            })

    # Ordenar por Data
    linhas.sort(key=lambda x: x["Data"])
    return pd.DataFrame(linhas)

# =============================================================================
#   FUNÇÕES AUXILIARES: DISPONIBILIDADE E CRIAÇÃO DE AGENDAMENTO
# =============================================================================

def verificar_disponibilidade(lab_id, data_ag, aulas):
    """
    Verifica conflitos com horários fixos e agendamentos aprovados.
    Retorna (True, set_conflitos) se houver conflito.
    """
    try:
        dia_semana = data_ag.weekday()
        indisponiveis = set()

        # Horários fixos
        fixos = supabase.table('horarios_fixos').select('*') \
            .eq('laboratorio_id', lab_id) \
            .eq('dia_semana', dia_semana).execute().data or []
        for f in fixos:
            dt_i = datetime.strptime(f['data_inicio'], "%Y-%m-%d").date()
            dt_f = datetime.strptime(f['data_fim'], "%Y-%m-%d").date()
            # Se a data de agendamento está dentro do período
            if dt_i <= data_ag <= dt_f:
                indisponiveis.update(f['aulas'])

        # Agendamentos aprovados
        aprovados = supabase.table('agendamentos').select('*') \
            .eq('laboratorio_id', lab_id) \
            .eq('data_agendamento', data_ag.isoformat()) \
            .eq('status','aprovado').execute().data or []
        for ap in aprovados:
            indisponiveis.update(ap['aulas'])

        confl = set(aulas) & indisponiveis
        if confl:
            return True, confl
        return False, None
    except Exception as e:
        st.error(f"Erro ao verificar disponibilidade: {e}")
        return True, None

def verificar_duplo_agendamento(usuario_id, laboratorio_id, data_ag, aulas):
    """
    Evita duplicar agendamento (status pendente) igual para o mesmo professor.
    """
    a_str = '{' + ','.join(map(str,aulas)) + '}'
    try:
        resp = supabase.table('agendamentos').select('*') \
              .eq('usuario_id', usuario_id) \
              .eq('laboratorio_id', laboratorio_id) \
              .eq('data_agendamento', data_ag.isoformat()) \
              .eq('aulas', a_str) \
              .eq('status','pendente').execute().data or []
        return len(resp) > 0
    except Exception as e:
        st.error(e)
        return True

def confirmar_agendamento_professor(lab_id, data_ag, aulas, desc):
    user_id = st.session_state.get("usuario_id")
    if not user_id:
        st.error("Usuário não autenticado. Faça login novamente.")
        return

    # Verifica se já existe um agendamento pendente igual
    if verificar_duplo_agendamento(user_id, lab_id, data_ag, aulas):
        st.error("Você já requisitou esse agendamento. Aguarde aprovação do administrador.")
        return

    novo = {
        "usuario_id": user_id,
        "laboratorio_id": lab_id,
        "data_agendamento": data_ag.isoformat(),
        "aulas": aulas,
        "descricao": desc,
        "status": "pendente"
    }
    try:
        supabase.table('agendamentos').insert(novo).execute()
        st.success("Agendamento solicitado com sucesso! Aguardando aprovação.")
    except Exception as e:
        st.error(f"Erro ao criar agendamento: {e}")

# =============================================================================
#                          FUNÇÃO LOGOUT
# =============================================================================

def efetuar_logout():
    """
    Limpa as variáveis de sessão e recarrega a aplicação.
    """
    st.session_state["autenticado"] = False
    st.session_state["tipo_usuario"] = None
    st.session_state["email"] = None
    st.session_state["usuario_id"] = None
    st.experimental_rerun()
