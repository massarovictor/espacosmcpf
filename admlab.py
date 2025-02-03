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
            st.subheader(lab['nome'])

            tab1, tab2, tab3 = st.tabs([
                "Agendamentos Pendentes", 
                "Horários Fixos", 
                "Agenda do Espaço"
            ])

            with tab1:
                gerenciar_agendamentos_pendentes(lab['id'])

            with tab2:
                gerenciar_horarios_fixos(lab['id'])

            with tab3:
                visualizar_agenda_laboratorio_admlab(lab['id'], lab['nome'])

    except Exception as e:
        st.error(f'Erro ao carregar os laboratórios: {e}')

    st.divider()
    if st.button("Logout"):
        efetuar_logout()

# =============================================================================
#                  GESTÃO DE AGENDAMENTOS PENDENTES
# =============================================================================

def gerenciar_agendamentos_pendentes(laboratorio_id):
    """
    Exibe agendamentos pendentes ordenados por ID (mais antigo -> mais novo),
    numerando cada solicitação e exibindo as opções de Aprovar/Rejeitar abaixo.
    """
    st.subheader("Agendamentos Pendentes")
    try:
        # Busca agendamentos pendentes do laboratório
        resp = supabase.table('agendamentos') \
                       .select('*') \
                       .eq('laboratorio_id', laboratorio_id) \
                       .eq('status', 'pendente') \
                       .execute()
        agendamentos = resp.data or []

        # Ordenação local por ID (o ID menor é o mais antigo)
        agendamentos.sort(key=lambda x: x['id'])

        if not agendamentos:
            st.info("Nenhum agendamento pendente.")
            return

        # Para numerar as solicitações do mais antigo (i=1) para o mais recente
        for i, ag in enumerate(agendamentos, start=1):
            # Em vez de mostrar o ID do agendamento no expander, mostramos "Solicitação #1", "#2", etc.
            with st.expander(f"Solicitação #{i}", expanded=False):
                exibir_agendamento_para_validacao(ag, i)

    except Exception as e:
        st.error(f"Erro ao carregar os agendamentos: {e}")

def exibir_agendamento_para_validacao(agendamento, num_solicitacao):
    """
    Exibe detalhes do agendamento e, abaixo, os botões Aprovar/Rejeitar.
    Recebe também o número da solicitação para uso opcional, se quiser exibir internamente.
    """
    try:
        # Buscar email do professor
        resp_user = supabase.table('users') \
                            .select('email') \
                            .eq('id', agendamento['usuario_id']) \
                            .execute().data
        professor_email = resp_user[0]['email'] if resp_user else "Desconhecido"

        # Aulas formatadas
        aulas_str = ", ".join([f"{a}ª Aula" for a in sorted(agendamento['aulas'])])

        # Exibe as informações em sequência
        st.write(f"**Professor:** {professor_email}")
        st.write(f"**Data Agendada:** {agendamento['data_agendamento']}")
        st.write(f"**Aulas:** {aulas_str}")
        st.write(f"**Status:** {agendamento['status']}")

        # Botões abaixo das informações
        colA, colB = st.columns(2)
        with colA:
            if st.button("✅ Aprovar", key=f"aprovar_{agendamento['id']}"):
                atualizar_status_agendamento(agendamento['id'], 'aprovado')
        with colB:
            if st.button("❌ Rejeitar", key=f"rejeitar_{agendamento['id']}"):
                atualizar_status_agendamento(agendamento['id'], 'rejeitado')

    except Exception as e:
        st.error(f"Erro ao exibir agendamento: {e}")

def atualizar_status_agendamento(agendamento_id, novo_status):
    """
    Atualiza status e recarrega a tela.
    """
    try:
        supabase.table('agendamentos') \
                .update({'status': novo_status}) \
                .eq('id', agendamento_id) \
                .execute()
        st.success(f"Agendamento atualizado com sucesso! (status: {novo_status})")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Erro ao atualizar o status: {e}")

# =============================================================================
#                        GESTÃO DE HORÁRIOS FIXOS
# =============================================================================

def gerenciar_horarios_fixos(laboratorio_id):
    st.subheader("Gerenciar Horários Fixos")
    DIAS_SEMANA_INVERSO = {
        0: 'Segunda',
        1: 'Terça',
        2: 'Quarta',
        3: 'Quinta',
        4: 'Sexta'
    }
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
        dias_semana_opcoes = {"Segunda":0,"Terça":1,"Quarta":2,"Quinta":3,"Sexta":4}
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
    from datetime import date

    st.markdown(
        """
        <style>
        [data-testid="stForm"] {
            max-width: 100% !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.container():
        st.markdown("### Editar Horário Fixo")

        with st.form(key=f'form_editar_horario_{h["id"]}'):
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
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar o horário fixo: {e}")

def remover_horario_fixo(h_id):
    try:
        supabase.table('horarios_fixos').delete().eq('id',h_id).execute()
        st.success("Horário fixo excluído!")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Erro ao remover horário: {e}")

def visualizar_agenda_laboratorio_admlab(lab_id, lab_nome):
    from datetime import date
    c1, c2 = st.columns(2)
    with c1:
        dt_i = st.date_input("Data Início", date.today())
    with c2:
        dt_f = st.date_input("Data Fim", date.today() + timedelta(days=7))

    if dt_i > dt_f:
        st.warning("A data de início não pode ser posterior à data de fim.")
        return

    if st.button("Consultar Agenda"):
        datas = [dt_i + timedelta(days=i) for i in range((dt_f - dt_i).days + 1)]

        hf = supabase.table('horarios_fixos').select('*') \
            .eq('laboratorio_id', lab_id).execute().data or []
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
