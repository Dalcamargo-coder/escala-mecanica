import streamlit as st
import os
from supabase import create_client, Client

# 1. Configuração da Página
st.set_page_config(
    page_title="Designações Mecânicas — Congregação Jardim América",
    page_icon="🏛️",
    layout="wide"
)

# 2. Conexão com o Supabase
SUPABASE_URL = "https://jwstginzuimrbvvavrlv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp3c3RnaW56dWltcmJ2dmF2cmx2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA2MjIwNDgsImV4cCI6MjEwNjE5ODA0OH0.XNLaxpWCElIntlXWS6_moHHCnzkTXUXBhcFoRx6K93M"

@st.cache_resource
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = get_supabase()
except Exception as e:
    st.error(f"Erro ao ligar ao banco de dados Supabase: {e}")
    st.stop()

# 3. Estado da Sessão
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""

if "user_role" not in st.session_state:
    st.session_state["user_role"] = None


# ============================================================
# TELA DE LOGIN / REGISTO
# ============================================================

if not st.session_state["logged_in"]:

    st.markdown(
        "<h1 style='text-align: center;'>🏛️ Portal de Designações Mecânicas</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='text-align: center; color: #6B7280;'>Congregação Jardim América</p>",
        unsafe_allow_html=True
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col2:

        tab_login, tab_cadastro = st.tabs(
            ["🔑 Entrar na Conta", "📝 Criar Nova Conta"]
        )

        # ----------------------------------------------------
        # LOGIN
        # ----------------------------------------------------

        with tab_login:

            st.subheader("Acesso dos Irmãos")

            email_login = st.text_input(
                "E-mail registado:",
                key="login_email"
            ).strip().lower()

            senha_login = st.text_input(
                "Palavra-passe:",
                type="password",
                key="login_senha"
            )

            if st.button(
                "Entrar no Portal",
                type="primary",
                use_container_width=True
            ):

                if email_login and senha_login:

                    try:

                        res = (
                            supabase
                            .table("usuarios")
                            .select("*")
                            .eq("email", email_login)
                            .eq("senha", senha_login)
                            .execute()
                        )

                        if res.data:

                            user = res.data[0]

                            if user.get("status") == "aprovado":

                                st.session_state["logged_in"] = True
                                st.session_state["user_name"] = user["nome"]
                                st.session_state["user_role"] = user["perfil"]

                                st.success(
                                    f"Bem-vindo, {user['nome']}!"
                                )

                                st.rerun()

                            elif user.get("status") == "pendente":

                                st.warning(
                                    "⏳ O seu registo ainda está pendente "
                                    "de autorização pelo Administrador."
                                )

                            else:

                                st.error(
                                    "❌ O seu pedido de acesso não foi aprovado."
                                )

                        else:

                            st.error(
                                "E-mail ou palavra-passe incorretos."
                            )

                    except Exception as err:

                        st.error(
                            f"Erro ao verificar conta: {err}"
                        )

                else:

                    st.warning(
                        "Preencha o e-mail e a palavra-passe."
                    )

        # ----------------------------------------------------
        # CADASTRO
        # ----------------------------------------------------

        with tab_cadastro:

            st.subheader("Registo de Novo Irmão")

            nome_cad = st.text_input(
                "Nome Completo:"
            )

            email_cad = st.text_input(
                "E-mail:"
            ).strip().lower()

            tel_cad = st.text_input(
                "WhatsApp (ex: 5519983035946):"
            ).strip()

            senha_cad = st.text_input(
                "Crie uma Palavra-passe:",
                type="password"
            )

            if st.button(
                "Enviar Pedido de Registo",
                use_container_width=True
            ):

                if nome_cad and email_cad and senha_cad and tel_cad:

                    try:

                        check = (
                            supabase
                            .table("usuarios")
                            .select("id")
                            .eq("email", email_cad)
                            .execute()
                        )

                        if check.data:

                            st.error(
                                "Este e-mail já está registado no sistema."
                            )

                        else:

                            (
                                supabase
                                .table("usuarios")
                                .insert({
                                    "nome": nome_cad,
                                    "email": email_cad,
                                    "telefone": tel_cad,
                                    "senha": senha_cad,
                                    "status": "pendente",
                                    "perfil": "irmao"
                                })
                                .execute()
                            )

                            st.success(
                                "✅ Registo enviado com sucesso! "
                                "Aguarde a aprovação."
                            )

                    except Exception as err:

                        st.error(
                            f"Erro ao realizar registo: {err}"
                        )

                else:

                    st.warning(
                        "Preencha todos os campos."
                    )


# ============================================================
# ÁREA INTERNA LOGADA
# ============================================================

else:

    st.sidebar.title("🏛️ Jardim América")

    st.sidebar.write(
        f"👤 **{st.session_state['user_name']}**"
    )

    st.sidebar.caption(
        f"Perfil: **{st.session_state['user_role'].upper()}**"
    )

    # --------------------------------------------------------
    # TERMINAR SESSÃO
    # --------------------------------------------------------

    if st.sidebar.button(
        "🚪 Terminar Sessão",
        use_container_width=True
    ):

        st.session_state["logged_in"] = False
        st.session_state["user_name"] = ""
        st.session_state["user_role"] = None

        st.rerun()

    # ========================================================
    # BUSCAR MESES
    # ========================================================

    try:

        res_meses = (
            supabase
            .table("escalas")
            .select("mes")
            .execute()
        )

        meses_disponiveis = (
            sorted(
                list(
                    set(
                        [
                            m["mes"]
                            for m in res_meses.data
                        ]
                    )
                )
            )
            if res_meses.data
            else ["2026-10"]
        )

    except Exception as err:

        st.sidebar.error(
            f"Erro ao buscar meses: {err}"
        )

        meses_disponiveis = ["2026-10"]

    if "2026-10" not in meses_disponiveis:

        meses_disponiveis.insert(
            0,
            "2026-10"
        )

    mes_selecionado = st.sidebar.selectbox(
        "📅 Selecionar Mês:",
        meses_disponiveis,
        index=0
    )

    # ========================================================
    # BUSCAR DADOS DA ESCALA
    # ========================================================

    try:

        res_escala = (
            supabase
            .table("escalas")
            .select("*")
            .eq("mes", mes_selecionado)
            .execute()
        )

        dados_escala = (
            res_escala.data
            if res_escala.data
            else []
        )

        # Mostrar quantas escalas foram encontradas
        st.sidebar.success(
            f"✅ {len(dados_escala)} escalas encontradas"
        )

    except Exception as err:

        dados_escala = []

        st.error(
            f"❌ Erro ao buscar escalas no Supabase: {err}"
        )

    # ========================================================
    # ORGANIZAR DATAS
    # ========================================================

    datas_dict = {}

    for item in dados_escala:

        dt = item["data_texto"]

        if dt not in datas_dict:

            datas_dict[dt] = []

        datas_dict[dt].append({
            "funcao": item["funcao"],
            "irmao": item["irmao"]
        })

    # ========================================================
    # CRIAR ABAS
    # ========================================================

    if st.session_state["user_role"] == "admin":

        tab1, tab2, tab3, tab4 = st.tabs([
            "📅 Escala do Mês",
            "🔍 Procurar por Irmão",
            "📄 Imprimir PDF",
            "⚙️ Gerir Escalas"
        ])

    else:

        tab1, tab2, tab3 = st.tabs([
            "📅 Escala do Mês",
            "🔍 Procurar por Irmão",
            "📄 Imprimir PDF"
        ])

        tab4 = None

    # ========================================================
    # ABA 1 - ESCALA DO MÊS
    # ========================================================

    with tab1:

        st.subheader(
            f"📋 Designações Mecânicas — {mes_selecionado}"
        )

        if not datas_dict:

            st.info(
                "Nenhuma escala registada no banco de dados para este mês."
            )

        else:

            lista_datas = list(
                datas_dict.keys()
            )

            for i in range(
                0,
                len(lista_datas),
                2
            ):

                c1, c2 = st.columns(2)

                dt1 = lista_datas[i]

                with c1:

                    st.info(
                        f"🔹 **{dt1}**"
                    )

                    for item in datas_dict[dt1]:

                        st.write(
                            f"**{item['funcao']}:** "
                            f"{item['irmao']}"
                        )

                if i + 1 < len(lista_datas):

                    dt2 = lista_datas[i + 1]

                    with c2:

                        st.success(
                            f"🟣 **{dt2}**"
                        )

                        for item in datas_dict[dt2]:

                            st.write(
                                f"**{item['funcao']}:** "
                                f"{item['irmao']}"
                            )

                st.divider()

    # ========================================================
    # ABA 2 - PROCURAR POR IRMÃO
    # ========================================================

    with tab2:

        st.subheader(
            "🔍 Minhas Designações"
        )

        busca = st.text_input(
            "Digite o nome para consultar:",
            value=st.session_state["user_name"]
        )

        if busca:

            encontrado = False

            for dt, itens in datas_dict.items():

                for item in itens:

                    if busca.lower() in item["irmao"].lower():

                        st.success(
                            f"📅 **{dt}** — "
                            f"**{item['funcao']}:** "
                            f"{item['irmao']}"
                        )

                        encontrado = True

            if not encontrado:

                st.warning(
                    "Nenhuma designação localizada para este nome."
                )

    # ========================================================
    # ABA 3 - PDF
    # ========================================================

    with tab3:

        st.subheader(
            "📄 Documento Oficial para Impressão"
        )

        pdf_path = (
            "Designações_Mecânicas_-_Outubro_2026.pdf"
        )

        if os.path.exists(pdf_path):

            with open(pdf_path, "rb") as f:

                st.download_button(
                    label="🖨️ Descarregar / Imprimir PDF Oficial",
                    data=f.read(),
                    file_name=pdf_path,
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )

        else:

            st.info(
                "O PDF oficial não foi encontrado no projeto."
            )

    # ========================================================
    # ABA 4 - ADMINISTRAR ESCALAS
    # ========================================================

    if tab4 is not None:

        with tab4:

            st.subheader(
                "⚙️ Cadastrar Nova Designação"
            )

            with st.form(
                "form_nova_designacao"
            ):

                c_mes, c_dia = st.columns(2)

                mes_input = c_mes.text_input(
                    "Mês (Ano-Mês):",
                    value="2026-11"
                )

                data_texto_input = c_dia.text_input(
                    "Data Formatada:",
                    value="Segunda-feira — 02/11/2026"
                )

                c_func, c_irm = st.columns(2)

                funcao_input = c_func.selectbox(
                    "Função:",
                    [
                        "🗣️ Oração Inicial",
                        "🗣️ Oração Final",
                        "📖 Leitor A Sentinela",
                        "🎤 Microfones",
                        "🚪 Ind. Entrada",
                        "🏛️ Ind. Auditório"
                    ]
                )

                irmao_input = c_irm.text_input(
                    "Nome do Irmão:"
                )

                dia_sem_input = st.selectbox(
                    "Tipo de Reunião:",
                    ["seg", "sab"],
                    format_func=lambda x:
                        "Segunda-feira"
                        if x == "seg"
                        else "Sábado"
                )

                if st.form_submit_button(
                    "➕ Adicionar à Escala",
                    type="primary",
                    use_container_width=True
                ):

                    if (
                        mes_input
                        and data_texto_input
                        and irmao_input
                    ):

                        try:

                            (
                                supabase
                                .table("escalas")
                                .insert({
                                    "mes": mes_input,
                                    "data_texto": data_texto_input,
                                    "dia_semana": dia_sem_input,
                                    "funcao": funcao_input,
                                    "irmao": irmao_input
                                })
                                .execute()
                            )

                            st.success(
                                "✅ Designação adicionada!"
                            )

                            st.rerun()

                        except Exception as err:

                            st.error(
                                f"Erro: {err}"
                            )

    # ========================================================
    # PAINEL DO ADMIN
    # ========================================================

    if st.session_state["user_role"] == "admin":

        st.sidebar.markdown("---")

        st.sidebar.subheader(
            "⚙️ Aprovar Utilizadores"
        )

        try:

            pendentes = (
                supabase
                .table("usuarios")
                .select("*")
                .eq("status", "pendente")
                .execute()
            )

            if pendentes.data:

                for u in pendentes.data:

                    st.sidebar.write(
                        f"👤 **{u['nome']}** "
                        f"({u.get('telefone', 'Sem tel')})"
                    )

                    c_ap, c_rec = st.sidebar.columns(2)

                    if c_ap.button(
                        "✅",
                        key=f"ap_{u['id']}"
                    ):

                        (
                            supabase
                            .table("usuarios")
                            .update({
                                "status": "aprovado"
                            })
                            .eq("id", u["id"])
                            .execute()
                        )

                        st.rerun()

                    if c_rec.button(
                        "❌",
                        key=f"rec_{u['id']}"
                    ):

                        (
                            supabase
                            .table("usuarios")
                            .update({
                                "status": "recusado"
                            })
                            .eq("id", u["id"])
                            .execute()
                        )

                        st.rerun()

        except Exception as err:

            st.sidebar.error(
                f"Erro ao carregar utilizadores: {err}"
            )
