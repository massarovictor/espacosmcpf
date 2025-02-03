import streamlit as st
from datetime import date, datetime, timedelta
import pandas as pd
from database import supabase

DIAS_SEMANA_INVERSO = {
    0: 'Segunda',
    1: 'Terça',
    2: 'Quarta',
    3: 'Quinta',
    4: 'Sexta'
}

def painel_admin_laboratorio():
    """
    Exibe o painel principal de administração de laboratórios 
    para o usuário do tipo 'admlab'.
    Possui três abas: Agendamentos Pendentes, Horários Fixos e Agenda do Laboratório.
    Inclui botões de Refresh e Logout no topo.
    """
    st.title("📅 Espaços MCPF")
    st.subheader("Painel de Administração dos Laboratórios")
    st.write("**EEEP Professora Maria Célia Pinheiro Falcão**")

    # Barra superior: Refresh e Logout
    with st.container():
        col1, col2, col3 = st.columns([4, 0.5, 1])
        with col1:
            st.write("")  # espaço ou outro texto
        with col2:
            if st.button("🔄", help="Recarregar a página"):
                st.experimental_rerun()
        with col3:
            if st.button("Logout"):
                efetuar_logout()

    administrador_id = st.session_state.get("usuario_id", None)

    try:
        # Buscar laboratórios do admlab
        response = supabase.table('laboratorios') \
                           .select('*') \
                           .eq('administrador_id', administrador_id) \
                           .execute()
        laboratorios = response.data or []

        if not laboratorios:
            st.info('Você não está associado(a) a nenhum laboratório.')
            return

        for lab in laboratorios:
            st.subheader(f"Laboratório de {lab['nome']}")

            tab1, tab2, tab3 = st.tabs(["Agendamentos Pendentes", "Horários Fixos", "Agenda do Laboratório"])

            with tab1:
                gerenciar_agendamentos_pendentes(lab['id'])

            with tab2:
                gerenciar_horarios_fixos(lab['id'])

            with tab3:
                visualizar_agenda_laboratorio_admlab(lab['id'], lab['nome'])

    except Exception as e:
        st.error(f'Erro ao carregar os laboratórios: {e}')

# =============================================================================
#                  GESTÃO DE AGENDAMENTOS PENDENTES
# =============================================================================

def gerenciar_agendamentos_pendentes(laboratorio_id):
    """
    Exibe agendamentos pendentes em formato “expander” (padrão anterior),
    ordenando localmente por ID para mostrar do mais antigo (ID menor) ao mais novo.
    """
    st.subheader("Agendamentos Pendentes (Mais antigos em cima)")
    try:
        resp = supabase.table('agendamentos') \
                       .select('*') \
                       .eq('laboratorio_id', laboratorio_id) \
                       .eq('status', 'pendente') \
                       .execute()
        agendamentos = resp.data or []

        # Ordenação local por ID crescente
        agendamentos.sort(key=lambda x: x['id'])

        if not agendamentos:
            st.info("Nenhum agendamento pendente.")
            return

        # Apresentação padrão em expanders
        for ag in agendamentos:
            with st.expander(f"Solicitação #{ag['id']}", expanded=False):
                exibir_agendamento_para_validacao(ag)

    except Exception as e:
        st.error(f"Erro ao carregar os agendamentos: {e}")

def exibir_agendamento_para_validacao(agendamento):
    """
    Layout padrão: colunas e botões Aprovar/Rejeitar sem dataframe.
    """
    try:
        # Buscar email do professor
        resp_user = supabase.table('users') \
                            .select('email') \
                            .eq('id', agendamento['usuario_id']) \
                            .execute().data
        professor_email = resp_user[0]['email'] if resp_user else "Desconhecido"
        
        aulas_str = ", ".join([f"{a}ª Aula" for a in sorted(agendamento['aulas'])])

        c1, c2 = st.columns([1.5, 2])
        with c1:
            st.write(f"**Professor:** {professor_email}")
            st.write(f"**Data Agendada:** {agendamento['data_agendamento']}")
            st.write(f"**Aulas:** {aulas_str}")
            st.write(f"**Status:** {agendamento['status']}")

        with c2:
            colA, colB = st.columns(2)
            with colA:
                if st.button(f"✅ Aprovar #{agendamento['id']}", key=f"aprovar_{agendamento['id']}"):
                    atualizar_status_agendamento(agendamento['id'], 'aprovado')
            with colB:
                if st.button(f"❌ Rejeitar #{agendamento['id']}", key=f"rejeitar_{agendamento['id']}"):
                    atualizar_status_agendamento(agendamento['id'], 'rejeitado')

    except Exception as e:
        st.error(f"Erro ao exibir agendamento: {e}")

def atualizar_status_agendamento(agendamento_id, novo_status):
    """
    Atualiza status e recarrega a tela.
    """
    try:
        supabase.table('agendamentos').update({'status': novo_status}).eq('id', agendamento_id).execute()
        st.success(f"Agendamento {agendamento_id} {novo_status} com sucesso!")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Erro ao atualizar o status: {e}")

# =============================================================================
#                        GESTÃO DE HORÁRIOS FIXOS
# =============================================================================

def gerenciar_horarios_fixos(laboratorio_id):
    """
    Exibe horários fixos no formato anterior (expander) e sem dataframe.
    """
    st.subheader("Gerenciar Horários Fixos")
    try:
        resp = supabase.table('horarios_fixos') \
                       .select('*') \
                       .eq('laboratorio_id', laboratorio_id) \
                       .execute()
        horarios = resp.data or []

        if horarios:
            horarios.sort(key=lambda x: x['dia_semana'])
            for h in horarios:
                dia_semana_nome = DIAS_SEMANA_INVERSO.get(h['dia_semana'], 'Desconhecido')
                aulas_str = ", ".join([f"{a}ª Aula" for a in sorted(h['aulas'])])
                periodo = f"{h['data_inicio']} até {h['data_fim']}"

                with st.expander(f"{dia_semana_nome} - {aulas_str}"):
                    st.write(f"**Período:** {periodo}")
                    st.write(f"**Descrição:** {h.get('descricao','')}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📝 Editar Horário", key=f"editar_{h['id']}"):
                            editar_horario_fixo(h)
                    with col2:
                        if st.button("❌ Excluir Horário", key=f"excluir_{h['id']}"):
                            remover_horario_fixo(h['id'])
        else:
            st.info("Nenhum horário fixo cadastrado.")

    except Exception as e:
        st.error(f"Erro ao carregar os horários fixos: {e}")

    st.markdown("---")
    st.subheader("Adicionar Novo Horário Fixo")
    adicionar_horario_fixo(laboratorio_id)

def adicionar_horario_fixo(lab_id):
    from datetime import date
    with st.form(key=f"form_novo_horario_{lab_id}"):
        dias_semana_opcoes = {
            "Segunda":0,"Terça":1,"Quarta":2,"Quinta":3,"Sexta":4
        }
        dia_nome = st.selectbox("Dia da Semana", options=list(dias_semana_opcoes.keys()))
        dia_semana = dias_semana_opcoes[dia_nome]
        aulas = st.multiselect("Aulas", list(range(1,10)))
        dt_i = st.date_input("Data Início", date.today())
        dt_f = st.date_input("Data Fim", date.today())
        desc = st.text_input("Descrição (opcional)")

        btn_submit = st.form_submit_button("✅ Adicionar Horário Fixo")
        if btn_submit:
            if not aulas:
                st.warning("Selecione ao menos 1 aula.")
            elif dt_i > dt_f:
                st.warning("Data de início não pode ser maior que data de fim.")
            else:
                novo = {
                    "laboratorio_id": lab_id,
                    "dia_semana": dia_semana,
                    "aulas": aulas,
                    "data_inicio": dt_i.isoformat(),
                    "data_fim": dt_f.isoformat(),
                    "descricao": desc.strip()
                }
                try:
                    supabase.table('horarios_fixos').insert(novo).execute()
                    st.success("Horário fixo adicionado!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Erro ao criar horário fixo: {e}")

def editar_horario_fixo(h):
    """
    Exibe um formulário para editar os dados de um horário fixo,
    sem mostrar o ID e ocupando a mesma largura dos demais componentes.
    """
    from datetime import date

    # CSS para deixar o st.form com largura total
    st.markdown(
        """
        <style>
        /* Seletor que identifica formulários no Streamlit */
        [data-testid="stForm"] {
            max-width: 100% !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Container opcional para agrupar esse bloco
    with st.container():
        st.markdown("### Editar Horário Fixo")  # Não exibimos o ID

        with st.form(key=f'form_editar_horario_{h["id"]}'):
            # Mapeamento dia da semana
            dias_semana_opcoes = {"Segunda":0,"Terça":1,"Quarta":2,"Quinta":3,"Sexta":4}
            dia_semana_nome_atual = {v:k for k,v in dias_semana_opcoes.items()}.get(h['dia_semana'],'Segunda')

            dia_semana_novo_nome = st.selectbox(
                "Dia da Semana:", 
                list(dias_semana_opcoes.keys()),
                index=list(dias_semana_opcoes.keys()).index(dia_semana_nome_atual)
                  if dia_semana_nome_atual in dias_semana_opcoes else 0
            )
            dia_semana_novo = dias_semana_opcoes[dia_semana_novo_nome]

            aulas_novas = st.multiselect("Selecione as Aulas:", list(range(1,10)), default=h['aulas'])
            dt_inicio = st.date_input("Data de Início:", value=date.fromisoformat(h['data_inicio']))
            dt_fim = st.date_input("Data de Fim:", value=date.fromisoformat(h['data_fim']))
            desc = st.text_input("Descrição (opcional):", value=h.get('descricao',''))

            submitted = st.form_submit_button("💾 Atualizar Horário Fixo")
            if submitted:
                if not aulas_novas:
                    st.warning("Por favor, selecione ao menos uma aula.")
                elif dt_inicio > dt_fim:
                    st.warning("A data de início não pode ser posterior à data de fim.")
                else:
                    horario_atualizado = {
                        'dia_semana': dia_semana_novo,
                        'aulas': aulas_novas,
                        'data_inicio': dt_inicio.isoformat(),
                        'data_fim': dt_fim.isoformat(),
                        'descricao': desc.strip()
                    }
                    try:
                        supabase.table('horarios_fixos') \
                                .update(horario_atualizado) \
                                .eq('id', h['id']) \
                                .execute()
                        st.success("Horário fixo atualizado com sucesso!")
                        st.rerun()  # Força recarregamento da página
                    except Exception as e:
                        st.error(f"Erro ao atualizar o horário fixo: {e}")

def remover_horario_fixo(h_id):
    try:
        supabase.table('horarios_fixos').delete().eq('id',h_id).execute()
        st.success("Horário fixo excluído!")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Erro ao remover horário: {e}")

# =============================================================================
#            AGENDA DO LABORATÓRIO (EXIBINDO EM DATAFRAME)
# =============================================================================

def visualizar_agenda_laboratorio_admlab(lab_id, lab_nome):
    """
    Usa DataFrame para exibir Horários Fixos + Agendamentos Aprovados
    em um intervalo de datas.
    """
    st.subheader(f"Agenda do {lab_nome}")

    c1, c2 = st.columns(2)
    with c1:
        dt_i = st.date_input("Data Início", date.today())
    with c2:
        dt_f = st.date_input("Data Fim", date.today() + timedelta(days=7))

    if dt_i > dt_f:
        st.warning("A data de início não pode ser posterior à data de fim.")
        return

    if st.button("Consultar Agenda"):
        # Montar lista de datas
        datas = [dt_i + timedelta(days=i) for i in range((dt_f - dt_i).days+1)]

        # Buscar horários fixos
        hf = supabase.table('horarios_fixos').select('*').eq('laboratorio_id', lab_id).execute().data or []
        # Buscar agendamentos aprovados
        ag = supabase.table('agendamentos').select('*') \
            .eq('laboratorio_id', lab_id).eq('status','aprovado') \
            .gte('data_agendamento', dt_i.isoformat()) \
            .lte('data_agendamento', dt_f.isoformat()) \
            .execute().data or []

        agenda_list = []

        # Processar horários fixos
        for h in hf:
            d_inicio = datetime.strptime(h['data_inicio'], "%Y-%m-%d").date()
            d_fim = datetime.strptime(h['data_fim'], "%Y-%m-%d").date()
            for d in datas:
                if d_inicio <= d <= d_fim and d.weekday() == h['dia_semana']:
                    aulas_str = ", ".join([f"{x}ª Aula" for x in sorted(h['aulas'])])
                    agenda_list.append({
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
                prof_email = buscar_email_usuario(a['usuario_id'])
                agenda_list.append({
                    "Data": d_ag.strftime("%Y-%m-%d"),
                    "Tipo": "Aprovado",
                    "Aulas": aulas_str,
                    "Professor": prof_email,
                    "Descrição": a.get("descricao","")
                })

        if not agenda_list:
            st.info("Nenhum horário fixo ou agendamento aprovado no intervalo selecionado.")
            return

        # Ordenar agenda_list por Data
        agenda_list.sort(key=lambda x: x["Data"])
        df_agenda = pd.DataFrame(agenda_list)

        st.dataframe(
            df_agenda,
            column_config={
                "Data": "Data",
                "Tipo": "Tipo (Fixo/Aprovado)",
                "Aulas": "Aulas",
                "Professor": "Professor",
                "Descrição": st.column_config.TextColumn("Descrição"),
            },
            hide_index=True,
            use_container_width=True
        )

def buscar_email_usuario(usuario_id):
    """
    Busca e retorna o email de um usuário dado o seu ID.
    """
    resp = supabase.table('users').select('email').eq('id', usuario_id).execute().data
    if resp:
        return resp[0]['email']
    return "Desconhecido"

def efetuar_logout():
    st.session_state["autenticado"] = False
    st.session_state["tipo_usuario"] = None
    st.session_state["email"] = None
    st.session_state["usuario_id"] = None
    st.experimental_rerun()
