import streamlit as st
import os
from datetime import datetime
from supabase import create_client, Client


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Designações Mecânicas",
    page_icon="🏛️",
    layout="wide"
)


# ============================================================
# CONEXÃO COM SUPABASE
# ============================================================

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

    supabase: Client = create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )

except Exception as err:
    st.error(
        f"Erro ao conectar ao banco de dados: {err}"
    )
    st.stop()


# ============================================================
# ESTILO
# ============================================================

st.markdown(
    """
    <style>

    .main {
        background-color: #f8fafc;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""

if "user_role" not in st.session_state:
    st.session_state["user_role"] = None


# ============================================================
# TELA DE LOGIN / CADASTRO
# ============================================================

if not st.session_state["logged_in"]:

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:20px;
        ">

            <h1>
                🏛️ Portal de Designações Mecânicas
            </h1>

            <p style="
                color:#6B7280;
                font-size:18px;
            ">
                Congregação Jardim América
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col2:

        tab_login, tab_cadastro = st.tabs(
            [
                "🔑 Entrar na Conta",
                "📝 Criar Nova Conta"
            ]
        )

        # ====================================================
        # LOGIN
        # ====================================================

        with tab_login:

            st.subheader(
                "Acesso dos Irmãos"
            )

            email_login = st.text_input(
                "E-mail registado:",
                key="login_email"
            ).strip().lower()

            senha_login = st.text_input(
                "Palavra-passe:",
                type="password",
                key="login_senha"
            ).strip()

            if st.button(
                "Entrar no Portal",
                type="primary",
                use_container_width=True
            ):

                if not email_login or not senha_login:

                    st.warning(
                        "Preencha o e-mail e a palavra-passe."
                    )

                else:

                    try:

                        # Buscar apenas pelo e-mail para validar corretamente
                        res = (
                            supabase
                            .table("usuarios")
                            .select("*")
                            .eq("email", email_login)
                            .execute()
                        )

                        if res.data:

                            user = res.data[0]

                            # Verificar se a senha corresponde
                            if user.get("senha") == senha_login:

                                if user.get("status") == "aprovado":

                                    st.session_state["logged_in"] = True

                                    st.session_state["user_name"] = (
                                        user["nome"]
                                    )

                                    st.session_state["user_role"] = (
                                        user["perfil"]
                                    )

                                    st.success(
                                        f"Bem-vindo, {user['nome']}!"
                                    )

                                    st.rerun()

                                elif user.get("status") == "pendente":

                                    st.warning(
                                        "⏳ O seu registo ainda está "
                                        "pendente de autorização."
                                    )

                                else:

                                    st.error(
                                        "❌ O seu pedido de acesso "
                                        "não foi aprovado."
                                    )

                            else:
                                st.error(
                                    "E-mail ou palavra-passe incorretos."
                                )

                        else:

                            st.error(
                                "E-mail ou palavra-passe incorretos."
                            )

                    except Exception as err:

                        st.error(
                            f"Erro ao verificar conta: {err}"
                        )


        # ====================================================
        # CADASTRO
        # ====================================================

        with tab_cadastro:

            st.subheader(
                "Registo de Novo Irmão"
            )

            nome_cad = st.text_input(
                "Nome Completo:"
            )

            email_cad = st.text_input(
                "E-mail:"
            ).strip().lower()

            tel_cad = st.text_input(
                "WhatsApp:"
            ).strip()

            senha_cad = st.text_input(
                "Crie uma Palavra-passe:",
                type="password"
            ).strip()

            if st.button(
                "Enviar Pedido de Registo",
                use_container_width=True
            ):

                if (
                    not nome_cad
                    or not email_cad
                    or not senha_cad
                    or not tel_cad
                ):

                    st.warning(
                        "Preencha todos os campos."
                    )

                else:

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
                                "Este e-mail já está registado."
                            )

                        else:

                            (
                                supabase
                                .table("usuarios")
                                .insert(
                                    {
                                        "nome": nome_cad,
                                        "email": email_cad,
                                        "telefone": tel_cad,
                                        "senha": senha_cad,
                                        "status": "pendente",
                                        "perfil": "irmao"
                                    }
                                )
                                .execute()
                            )

                            st.success(
                                "✅ Registo enviado! "
                                "Aguarde a aprovação."
                            )

                    except Exception as err:

                        st.error(
                            f"Erro ao realizar registo: {err}"
                        )


# ============================================================
# ÁREA INTERNA
# ============================================================

else:

    # ========================================================
    # BARRA LATERAL
    # ========================================================

    st.sidebar.title(
        "🏛️ Jardim América"
    )

    st.sidebar.write(
        f"👤 **{st.session_state['user_name']}**"
    )

    st.sidebar.caption(
        f"Perfil: **{st.session_state['user_role'].upper()}**"
    )

    if st.sidebar.button(
        "🚪 Sair",
        use_container_width=True
    ):

        st.session_state["logged_in"] = False
        st.session_state["user_name"] = ""
        st.session_state["user_role"] = None

        st.rerun()


    # ========================================================
    # BUSCAR MESES DISPONÍVEIS
    # ========================================================

    try:

        res_meses = (
            supabase
            .table("escalas")
            .select("mes")
            .execute()
        )

        meses = []

        for item in res_meses.data or []:

            mes = item.get("mes")

            if mes and mes not in meses:
                meses.append(mes)

        meses = sorted(meses)

    except Exception as err:

        st.error(
            f"Erro ao carregar os meses: {err}"
        )

        meses = []


    if not meses:

        st.warning(
            "Nenhum mês possui designações cadastradas."
        )

        st.stop()


    nomes_meses = {
        "01": "Janeiro",
        "02": "Fevereiro",
        "03": "Março",
        "04": "Abril",
        "05": "Maio",
        "06": "Junho",
        "07": "Julho",
        "08": "Agosto",
        "09": "Setembro",
        "10": "Outubro",
        "11": "Novembro",
        "12": "Dezembro"
    }


    def nome_mes(mes):

        try:

            ano, numero = mes.split("-")

            return (
                f"{nomes_meses.get(numero, numero)} "
                f"de {ano}"
            )

        except Exception:

            return mes


    mes_selecionado = st.sidebar.selectbox(
        "📅 Selecionar mês:",
        meses,
        format_func=nome_mes
    )


    try:

        res = (
            supabase
            .table("escalas")
            .select("*")
            .eq("mes", mes_selecionado)
            .execute()
        )

        registros = res.data or []

    except Exception as err:

        st.error(
            f"Erro ao carregar a escala: {err}"
        )

        registros = []


    datas_dict = {}

    for item in registros:

        data = item.get("data_texto")

        if not data:
            continue

        if data not in datas_dict:
            datas_dict[data] = []

        datas_dict[data].append(item)


    def data_para_datetime(data_texto):

        try:

            return datetime.strptime(
                data_texto,
                "%d/%m/%Y"
            )

        except Exception:

            return datetime.max


    lista_datas = sorted(
        datas_dict.keys(),
        key=data_para_datetime
    )


    st.markdown(
        f"""
        <div style="
            background:linear-gradient(
                135deg,
                #1e3a8a,
                #2563eb
            );
            padding:25px;
            border-radius:15px;
            margin-bottom:25px;
            color:white;
            box-shadow:0 4px 12px
            rgba(0,0,0,0.15);
        ">

            <h2 style="
                margin:0;
                color:white;
            ">
                📋 Designações Mecânicas
            </h2>

            <p style="
                margin:8px 0 0 0;
                font-size:18px;
            ">
                Congregação Jardim América
            </p>

            <p style="
                margin:6px 0 0 0;
                font-size:16px;
                opacity:0.9;
            ">
                📅 {nome_mes(mes_selecionado)}
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )


    if st.session_state["user_role"] == "admin":

        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "📅 Escala do Mês",
                "🔍 Procurar por Irmão",
                "📄 Imprimir PDF",
                "⚙️ Gerir Escalas"
            ]
        )

    else:

        tab1, tab2, tab3 = st.tabs(
            [
                "📅 Escala do Mês",
                "🔍 Procurar por Irmão",
                "📄 Imprimir PDF"
            ]
        )

        tab4 = None


    with tab1:

        if not datas_dict:

            st.info(
                "Nenhuma escala registada "
                "no banco de dados para este mês."
            )

        else:

            for i in range(
                0,
                len(lista_datas),
                2
            ):

                col1, col2 = st.columns(2)

                dt1 = lista_datas[i]

                with col1:

                    try:

                        data_obj = datetime.strptime(
                            dt1,
                            "%d/%m/%Y"
                        )

                        dias_semana = [
                            "Segunda-feira",
                            "Terça-feira",
                            "Quarta-feira",
                            "Quinta-feira",
                            "Sexta-feira",
                            "Sábado",
                            "Domingo"
                        ]

                        dia_semana = dias_semana[
                            data_obj.weekday()
                        ]

                    except Exception:

                        dia_semana = ""

                    html1 = f"""
                    <div style="
                        background:#ffffff;
                        border-radius:15px;
                        padding:20px;
                        margin-bottom:20px;
                        border-left:6px solid #1e3a8a;
                        box-shadow:
                            0 3px 10px
                            rgba(0,0,0,0.10);
                    ">

                        <h3 style="
                            margin:0 0 18px 0;
                            color:#1e3a8a;
                            font-size:18px;
                        ">
                            🔵 {dia_semana} — {dt1}
                        </h3>
                    """

                    for item in datas_dict[dt1]:

                        html1 += f"""
                        <div style="
                            margin-bottom:12px;
                        ">

                            <strong style="
                                color:#111827;
                            ">
                                {item.get('funcao', '')}
                            </strong>

                            <br>

                            <span style="
                                color:#374151;
                                font-size:16px;
                            ">
                                {item.get('irmao', '')}
                            </span>

                        </div>
                        """

                    html1 += """
                    </div>
                    """

                    st.markdown(
                        html1,
                        unsafe_allow_html=True
                    )

                if i + 1 < len(lista_datas):

                    dt2 = lista_datas[i + 1]

                    with col2:

                        try:

                            data_obj = datetime.strptime(
                                dt2,
                                "%d/%m/%Y"
                            )

                            dias_semana = [
                                "Segunda-feira",
                                "Terça-feira",
                                "Quarta-feira",
                                "Quinta-feira",
                                "Sexta-feira",
                                "Sábado",
                                "Domingo"
                            ]

                            dia_semana = dias_semana[
                                data_obj.weekday()
                            ]

                        except Exception:

                            dia_semana = ""

                        html2 = f"""
                        <div style="
                            background:#ffffff;
                            border-radius:15px;
                            padding:20px;
                            margin-bottom:20px;
                            border-left:6px solid #7e22ce;
                            box-shadow:
                                0 3px 10px
                                rgba(0,0,0,0.10);
                        ">

                            <h3 style="
                                margin:0 0 18px 0;
                                color:#7e22ce;
                                font-size:18px;
                            ">
                                🟣 {dia_semana} — {dt2}
                            </h3>
                        """

                        for item in datas_dict[dt2]:

                            html2 += f"""
                            <div style="
                                margin-bottom:12px;
                            ">

                                <strong style="
                                    color:#111827;
                                ">
                                    {item.get('funcao', '')}
                                </strong>

                                <br>

                                <span style="
                                    color:#374151;
                                    font-size:16px;
                                ">
                                    {item.get('irmao', '')}
                                </span>

                            </div>
                            """

                        html2 += """
                        </div>
                        """

                        st.markdown(
                            html2,
                            unsafe_allow_html=True
                        )


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

            for dt in lista_datas:

                itens = datas_dict[dt]

                for item in itens:

                    nome_irmao = str(
                        item.get(
                            "irmao",
                            ""
                        )
                    )

                    if (
                        busca.lower()
                        in nome_irmao.lower()
                    ):

                        st.success(
                            f"📅 **{dt}** — "
                            f"**{item.get('funcao', '')}:** "
                            f"{item.get('irmao', '')}"
                        )

                        encontrado = True

            if not encontrado:

                st.warning(
                    "Nenhuma designação localizada "
                    "para este nome."
                )


    with tab3:

        st.subheader(
            "📄 Documento Oficial para Impressão"
        )

        pdf_path = (
            "Designações_Mecânicas_-_Outubro_2026.pdf"
        )

        if os.path.exists(pdf_path):

            with open(
                pdf_path,
                "rb"
            ) as f:

                st.download_button(
                    label=(
                        "🖨️ Descarregar / "
                        "Imprimir PDF Oficial"
                    ),
                    data=f.read(),
                    file_name=pdf_path,
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )

        else:

            st.info(
                "O PDF oficial não foi encontrado "
                "no projeto."
            )


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
                    value=mes_selecionado
                )

                data_texto_input = c_dia.text_input(
                    "Data Formatada:",
                    placeholder="Ex.: 05/10/2026"
                )

                dia_semana_input = st.selectbox(
                    "Dia da Semana:",
                    [
                        "seg",
                        "sab"
                    ]
                )

                funcao_input = st.selectbox(
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

                irmao_input = st.text_input(
                    "Nome do Irmão:"
                )

                salvar = st.form_submit_button(
                    "💾 Salvar Designação",
                    use_container_width=True
                )

            if salvar:

                if (
                    not mes_input.strip()
                    or not data_texto_input.strip()
                    or not irmao_input.strip()
                ):

                    st.warning(
                        "Preencha todos os campos."
                    )

                else:

                    try:

                        datetime.strptime(
                            data_texto_input.strip(),
                            "%d/%m/%Y"
                        )

                        existente = (
                            supabase
                            .table("escalas")
                            .select("id")
                            .eq(
                                "mes",
                                mes_input.strip()
                            )
                            .eq(
                                "data_texto",
                                data_texto_input.strip()
                            )
                            .eq(
                                "funcao",
                                funcao_input
                            )
                            .eq(
                                "irmao",
                                irmao_input.strip()
                            )
                            .execute()
                        )

                        if existente.data:

                            st.warning(
                                "Esta designação já está cadastrada."
                            )

                        else:

                            (
                                supabase
                                .table("escalas")
                                .insert(
                                    {
                                        "mes": mes_input.strip(),
                                        "data_texto": data_texto_input.strip(),
                                        "dia_semana": dia_semana_input,
                                        "funcao": funcao_input,
                                        "irmao": irmao_input.strip()
                                    }
                                )
                                .execute()
                            )

                            st.success(
                                "✅ Designação cadastrada com sucesso!"
                            )

                            st.rerun()

                    except ValueError:

                        st.error(
                            "A data deve estar no formato "
                            "DD/MM/AAAA. Exemplo: 05/10/2026"
                        )

                    except Exception as err:

                        st.error(
                            f"Erro ao cadastrar designação: {err}"
                        )

            st.divider()

            st.subheader(
                "📋 Designações cadastradas"
            )

            if registros:

                for item in sorted(
                    registros,
                    key=lambda x: data_para_datetime(
                        x.get(
                            "data_texto",
                            ""
                        )
                    )
                ):

                    data_item = item.get(
                        "data_texto",
                        ""
                    )

                    funcao_item = item.get(
                        "funcao",
                        ""
                    )

                    irmao_item = item.get(
                        "irmao",
                        ""
                    )

                    st.write(
                        f"📅 **{data_item}** — "
                        f"{funcao_item} — "
                        f"**{irmao_item}**"
                    )

            else:

                st.info(
                    "Não existem designações neste mês."
                )


    if st.session_state["user_role"] == "admin":

        st.sidebar.divider()

        st.sidebar.subheader(
            "👥 Utilizadores"
        )

        try:

            usuarios = (
                supabase
                .table("usuarios")
                .select("*")
                .execute()
            )

            lista_usuarios = usuarios.data or []

            pendentes = [
                u
                for u in lista_usuarios
                if u.get("status") == "pendente"
            ]

            if pendentes:

                st.sidebar.warning(
                    f"{len(pendentes)} "
                    f"pedido(s) pendente(s)"
                )

                for usuario in pendentes:

                    with st.sidebar.expander(
                        usuario.get(
                            "nome",
                            "Sem nome"
                        )
                    ):

                        st.write(
                            usuario.get(
                                "email",
                                ""
                            )
                        )

                        st.write(
                            usuario.get(
                                "telefone",
                                ""
                            )
                        )

                        col_a, col_b = st.columns(2)

                        with col_a:

                            if st.button(
                                "✅ Aprovar",
                                key=f"aprovar_{usuario['id']}"
                            ):

                                (
                                    supabase
                                    .table("usuarios")
                                    .update(
                                        {
                                            "status": "aprovado"
                                        }
                                    )
                                    .eq(
                                        "id",
                                        usuario["id"]
                                    )
                                    .execute()
                                )

                                st.success(
                                    "Utilizador aprovado."
                                )

                                st.rerun()

                        with col_b:

                            if st.button(
                                "❌ Rejeitar",
                                key=f"rejeitar_{usuario['id']}"
                            ):

                                (
                                    supabase
                                    .table("usuarios")
                                    .update(
                                        {
                                            "status": "rejeitado"
                                        }
                                    )
                                    .eq(
                                        "id",
                                        usuario["id"]
                                    )
                                    .execute()
                                )

                                st.warning(
                                    "Utilizador rejeitado."
                                )

                                st.rerun()

            else:

                st.sidebar.caption(
                    "Nenhum pedido pendente."
                )

        except Exception as err:

            st.sidebar.error(
                f"Erro ao carregar utilizadores: {err}"
            )
