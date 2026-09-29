import os
import re
from datetime import datetime
from html import escape

import streamlit as st
from supabase import create_client, Client


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Designações Mecânicas — Congregação Jardim América",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# ESTILO VISUAL
# ============================================================

st.markdown(
    """
    <style>

    /* Fundo geral */
    .stApp {
        background-color: #f8fafc;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f1f5f9;
    }

    /* Botões */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
    }

    /* Caixa de informação */
    .info-card {
        background: white;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 18px;
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.08);
    }

    /* Cabeçalho principal */
    .main-header {
        background: linear-gradient(
            135deg,
            #1e3a8a,
            #2563eb
        );
        padding: 28px;
        border-radius: 18px;
        margin-bottom: 25px;
        color: white;
        box-shadow: 0 5px 18px rgba(0, 0, 0, 0.15);
    }

    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 30px;
    }

    .main-header p {
        margin: 6px 0 0 0;
    }

    /* Cabeçalho das reuniões */
    .meeting-title {
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 18px;
    }

    /* Item da designação */
    .assignment {
        padding: 10px 0;
        border-bottom: 1px solid #e5e7eb;
    }

    .assignment:last-child {
        border-bottom: none;
    }

    .assignment-function {
        font-weight: 700;
        color: #111827;
        font-size: 15px;
    }

    .assignment-name {
        color: #374151;
        font-size: 16px;
        margin-top: 4px;
    }

    /* Login */
    .login-title {
        text-align: center;
        padding: 15px;
    }

    /* Pequenos textos */
    .muted {
        color: #6b7280;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CONFIGURAÇÃO DO SUPABASE
# ============================================================

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

except Exception:
    st.error(
        """
        ⚠️ As configurações do Supabase não foram encontradas.

        Configure `SUPABASE_URL` e `SUPABASE_KEY`
        nos Secrets do seu aplicativo no Streamlit Cloud.
        """
    )
    st.stop()


@st.cache_resource
def get_supabase() -> Client:
    return create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )


try:
    supabase = get_supabase()

except Exception:
    st.error(
        "⚠️ Não foi possível conectar ao banco de dados."
    )
    st.stop()


# ============================================================
# ESTADO DA SESSÃO
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""

if "user_role" not in st.session_state:
    st.session_state["user_role"] = None

if "user_id" not in st.session_state:
    st.session_state["user_id"] = None


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def validar_email(email: str) -> bool:
    """
    Validação simples de e-mail.
    """
    padrao = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(padrao, email))


def converter_data(data_texto: str):
    """
    Tenta encontrar uma data no formato DD/MM/YYYY
    dentro do texto da reunião.

    Exemplos aceitos:
    Segunda-feira — 05/10/2026
    Sábado — 10/10/2026
    """

    if not data_texto:
        return None

    encontrado = re.search(
        r"(\d{2})/(\d{2})/(\d{4})",
        str(data_texto)
    )

    if not encontrado:
        return None

    try:
        dia = int(encontrado.group(1))
        mes = int(encontrado.group(2))
        ano = int(encontrado.group(3))

        return datetime(
            ano,
            mes,
            dia
        )

    except ValueError:
        return None


def nome_dia_semana(data):
    """
    Retorna o nome do dia da semana.
    """

    if data is None:
        return ""

    dias = {
        0: "Segunda-feira",
        1: "Terça-feira",
        2: "Quarta-feira",
        3: "Quinta-feira",
        4: "Sexta-feira",
        5: "Sábado",
        6: "Domingo"
    }

    return dias.get(
        data.weekday(),
        ""
    )


def normalizar_data_texto(
    data_texto: str,
    dia_semana: str = ""
) -> str:
    """
    Mantém o texto original quando possível,
    mas evita repetir o nome do dia.
    """

    data = converter_data(data_texto)

    if data is None:
        return str(data_texto or "Data não informada")

    dia = nome_dia_semana(data)

    return f"{dia} — {data.strftime('%d/%m/%Y')}"


def chave_ordenacao_reuniao(item):
    """
    Ordenação cronológica real.

    Caso a data não possa ser identificada,
    joga o registro para o final.
    """

    data_texto = item.get(
        "data_texto",
        ""
    )

    data = converter_data(
        str(data_texto)
    )

    if data is None:
        return (
            datetime.max,
            str(data_texto)
        )

    return (
        data,
        str(data_texto)
    )


def ordenar_dados_escala(dados):
    """
    Ordena todos os registros pela data real.
    """

    return sorted(
        dados,
        key=chave_ordenacao_reuniao
    )


def montar_datas(dados):
    """
    Agrupa as designações por reunião/data.
    """

    datas = {}

    dados_ordenados = ordenar_dados_escala(
        dados
    )

    for item in dados_ordenados:

        data_texto = str(
            item.get(
                "data_texto",
                "Data não informada"
            )
        ).strip()

        if not data_texto:
            data_texto = "Data não informada"

        if data_texto not in datas:
            datas[data_texto] = []

        datas[data_texto].append(
            item
        )

    return datas


def obter_cor_reuniao(item):
    """
    Define a cor de acordo com o dia da semana.
    """

    dia_semana = str(
        item.get(
            "dia_semana",
            ""
        )
    ).lower().strip()

    if dia_semana == "sab":
        return "#7e22ce"

    if dia_semana == "seg":
        return "#1e3a8a"

    data = converter_data(
        str(
            item.get(
                "data_texto",
                ""
            )
        )
    )

    if data is not None:

        if data.weekday() == 5:
            return "#7e22ce"

        if data.weekday() == 0:
            return "#1e3a8a"

    return "#2563eb"


def obter_icone_reuniao(item):
    """
    Define o ícone da reunião.
    """

    dia_semana = str(
        item.get(
            "dia_semana",
            ""
        )
    ).lower().strip()

    if dia_semana == "sab":
        return "🟣"

    if dia_semana == "seg":
        return "🔵"

    data = converter_data(
        str(
            item.get(
                "data_texto",
                ""
            )
        )
    )

    if data is not None:

        if data.weekday() == 5:
            return "🟣"

        if data.weekday() == 0:
            return "🔵"

    return "📅"


def obter_titulo_reuniao(
    data_texto,
    itens
):
    """
    Cria um título limpo:

    📅 Segunda-feira — 05/10/2026

    sem repetir o nome do dia.
    """

    data = converter_data(
        str(data_texto)
    )

    if data is not None:

        dia = nome_dia_semana(
            data
        )

        return (
            f"{dia} — "
            f"{data.strftime('%d/%m/%Y')}"
        )

    for item in itens:

        dia_semana = str(
            item.get(
                "dia_semana",
                ""
            )
        ).lower().strip()

        if dia_semana == "sab":
            return f"Sábado — {data_texto}"

        if dia_semana == "seg":
            return f"Segunda-feira — {data_texto}"

    return str(data_texto)


def obter_mes_nome(mes):
    """
    Converte YYYY-MM para um nome amigável.
    """

    nomes = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro"
    }

    try:

        partes = str(
            mes
        ).split("-")

        ano = int(partes[0])
        numero = int(partes[1])

        return (
            f"{nomes.get(numero, str(numero))} "
            f"de {ano}"
        )

    except Exception:
        return str(mes)


# ============================================================
# TELA DE LOGIN / CADASTRO
# ============================================================

if not st.session_state["logged_in"]:

    st.markdown(
        """
        <div class="login-title">

            <h1>
                🏛️ Portal de Designações Mecânicas
            </h1>

            <p class="muted" style="font-size:18px;">
                Congregação Jardim América
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    col1, col2, col3 = st.columns(
        [1, 1.4, 1]
    )

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
            )

            if st.button(
                "Entrar no Portal",
                type="primary",
                use_container_width=True
            ):

                if (
                    not email_login
                    or not senha_login
                ):

                    st.warning(
                        "Preencha o e-mail e a palavra-passe."
                    )

                elif not validar_email(
                    email_login
                ):

                    st.warning(
                        "Digite um e-mail válido."
                    )

                else:

                    try:

                        res = (
                            supabase
                            .table("usuarios")
                            .select(
                                "id,nome,email,senha,"
                                "telefone,status,perfil"
                            )
                            .eq(
                                "email",
                                email_login
                            )
                            .eq(
                                "senha",
                                senha_login
                            )
                            .execute()
                        )

                        if res.data:

                            user = res.data[0]

                            status = user.get(
                                "status"
                            )

                            if status == "aprovado":

                                st.session_state[
                                    "logged_in"
                                ] = True

                                st.session_state[
                                    "user_name"
                                ] = user.get(
                                    "nome",
                                    ""
                                )

                                st.session_state[
                                    "user_role"
                                ] = user.get(
                                    "perfil",
                                    "irmao"
                                )

                                st.session_state[
                                    "user_id"
                                ] = user.get(
                                    "id"
                                )

                                st.success(
                                    f"Bem-vindo, "
                                    f"{user.get('nome', '')}!"
                                )

                                st.rerun()

                            elif status == "pendente":

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

                    except Exception:

                        st.error(
                            "Não foi possível verificar a conta."
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
            ).strip()

            email_cad = st.text_input(
                "E-mail:"
            ).strip().lower()

            tel_cad = st.text_input(
                "WhatsApp:"
            ).strip()

            senha_cad = st.text_input(
                "Crie uma Palavra-passe:",
                type="password"
            )

            confirmar_senha = st.text_input(
                "Confirme a Palavra-passe:",
                type="password"
            )

            if st.button(
                "Enviar Pedido de Registo",
                use_container_width=True
            ):

                if (
                    not nome_cad
                    or not email_cad
                    or not senha_cad
                    or not confirmar_senha
                    or not tel_cad
                ):

                    st.warning(
                        "Preencha todos os campos."
                    )

                elif not validar_email(
                    email_cad
                ):

                    st.warning(
                        "Digite um e-mail válido."
                    )

                elif len(senha_cad) < 6:

                    st.warning(
                        "A palavra-passe deve ter pelo menos 6 caracteres."
                    )

                elif senha_cad != confirmar_senha:

                    st.warning(
                        "As palavras-passe não coincidem."
                    )

                else:

                    try:

                        check = (
                            supabase
                            .table("usuarios")
                            .select("id")
                            .eq(
                                "email",
                                email_cad
                            )
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
                                "✅ Registo enviado! "
                                "Aguarde a aprovação."
                            )

                    except Exception:

                        st.error(
                            "Não foi possível realizar o registo."
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

    perfil_atual = str(
        st.session_state.get(
            "user_role",
            "irmao"
        )
    ).upper()

    st.sidebar.caption(
        f"Perfil: **{perfil_atual}**"
    )

    if st.sidebar.button(
        "🚪 Terminar Sessão",
        use_container_width=True
    ):

        st.session_state["logged_in"] = False
        st.session_state["user_name"] = ""
        st.session_state["user_role"] = None
        st.session_state["user_id"] = None

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

        meses_disponiveis = sorted(
            list(
                set(
                    str(
                        item.get("mes")
                    ).strip()
                    for item in (
                        res_meses.data or []
                    )
                    if item.get("mes")
                )
            ),
            reverse=True
        )

    except Exception:

        meses_disponiveis = []

        st.sidebar.error(
            "Não foi possível carregar os meses."
        )


    # ========================================================
    # SE NÃO EXISTIREM MESES
    # ========================================================

    if not meses_disponiveis:

        st.warning(
            "Nenhuma escala foi cadastrada no banco de dados."
        )

        if st.session_state["user_role"] == "admin":

            st.info(
                "Como administrador, utilize "
                "\"⚙️ Gerir Escalas\" para cadastrar a primeira escala."
            )

        st.stop()


    # ========================================================
    # SELECIONAR MÊS
    # ========================================================

    mes_selecionado = st.sidebar.selectbox(
        "📅 Selecionar Mês:",
        meses_disponiveis,
        format_func=obter_mes_nome
    )


    # ========================================================
    # BUSCAR ESCALAS
    # ========================================================

    try:

        res_escala = (
            supabase
            .table("escalas")
            .select(
                "id,mes,data_texto,dia_semana,funcao,irmao"
            )
            .eq(
                "mes",
                str(
                    mes_selecionado
                ).strip()
            )
            .execute()
        )

        dados_escala = (
            res_escala.data or []
        )

        dados_escala = ordenar_dados_escala(
            dados_escala
        )

        st.sidebar.success(
            f"✅ {len(dados_escala)} registros encontrados"
        )

    except Exception:

        dados_escala = []

        st.sidebar.error(
            "Não foi possível carregar a escala."
        )


    # ========================================================
    # ORGANIZAR DATAS
    # ========================================================

    datas_dict = montar_datas(
        dados_escala
    )


    # ========================================================
    # ABAS
    # ========================================================

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


    # ========================================================
    # ABA 1 — ESCALA DO MÊS
    # ========================================================

    with tab1:

        st.markdown(
            f"""
            <div class="main-header">

                <h1>
                    📋 Designações Mecânicas
                </h1>

                <p style="font-size:18px;">
                    Congregação Jardim América
                </p>

                <p style="font-size:16px; opacity:0.9;">
                    📅 {escape(obter_mes_nome(mes_selecionado))}
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )


        if not datas_dict:

            st.info(
                "Nenhuma escala registada "
                "no banco de dados para este mês."
            )


        else:

            # ------------------------------------------------
            # LISTA DE REUNIÕES JÁ ORDENADA
            # ------------------------------------------------

            lista_datas = list(
                datas_dict.keys()
            )

            # ------------------------------------------------
            # DUAS COLUNAS
            # ------------------------------------------------

            for i in range(
                0,
                len(lista_datas),
                2
            ):

                col1, col2 = st.columns(
                    2,
                    gap="large"
                )


                # ============================================
                # PRIMEIRA REUNIÃO
                # ============================================

                dt1 = lista_datas[i]
                itens1 = datas_dict[dt1]

                item_referencia1 = itens1[0]

                cor1 = obter_cor_reuniao(
                    item_referencia1
                )

                icone1 = obter_icone_reuniao(
                    item_referencia1
                )

                titulo1 = obter_titulo_reuniao(
                    dt1,
                    itens1
                )

                with col1:

                    html1 = f"""
                    <div class="info-card"
                         style="
                            border-left:6px solid {cor1};
                         ">

                        <div class="meeting-title"
                             style="
                                color:{cor1};
                             ">

                            {icone1} {escape(titulo1)}

                        </div>
                    """

                    for item in itens1:

                        funcao = escape(
                            str(
                                item.get(
                                    "funcao",
                                    ""
                                )
                            )
                        )

                        irmao = escape(
                            str(
                                item.get(
                                    "irmao",
                                    ""
                                )
                            )
                        )

                        html1 += f"""
                        <div class="assignment">

                            <div class="assignment-function">
                                {funcao}
                            </div>

                            <div class="assignment-name">
                                {irmao}
                            </div>

                        </div>
                        """

                    html1 += """
                    </div>
                    """

                    st.markdown(
                        html1,
                        unsafe_allow_html=True
                    )


                # ============================================
                # SEGUNDA REUNIÃO
                # ============================================

                if i + 1 < len(lista_datas):

                    dt2 = lista_datas[i + 1]

                    itens2 = datas_dict[
                        dt2
                    ]

                    item_referencia2 = itens2[0]

                    cor2 = obter_cor_reuniao(
                        item_referencia2
                    )

                    icone2 = obter_icone_reuniao(
                        item_referencia2
                    )

                    titulo2 = obter_titulo_reuniao(
                        dt2,
                        itens2
                    )

                    with col2:

                        html2 = f"""
                        <div class="info-card"
                             style="
                                border-left:6px solid {cor2};
                             ">

                            <div class="meeting-title"
                                 style="
                                    color:{cor2};
                                 ">

                                {icone2} {escape(titulo2)}

                            </div>
                        """

                        for item in itens2:

                            funcao = escape(
                                str(
                                    item.get(
                                        "funcao",
                                        ""
                                    )
                                )
                            )

                            irmao = escape(
                                str(
                                    item.get(
                                        "irmao",
                                        ""
                                    )
                                )
                            )

                            html2 += f"""
                            <div class="assignment">

                                <div class="assignment-function">
                                    {funcao}
                                </div>

                                <div class="assignment-name">
                                    {irmao}
                                </div>

                            </div>
                            """

                        html2 += """
                        </div>
                        """

                        st.markdown(
                            html2,
                            unsafe_allow_html=True
                        )


    # ========================================================
    # ABA 2 — PROCURAR POR IRMÃO
    # ========================================================

    with tab2:

        st.subheader(
            "🔍 Procurar por Irmão"
        )

        st.caption(
            "Consulte as designações cadastradas para o mês selecionado."
        )

        busca = st.text_input(
            "Digite o nome para consultar:",
            value=st.session_state["user_name"],
            placeholder="Ex.: João Silva"
        ).strip()

        if busca:

            resultados = []

            for dt, itens in datas_dict.items():

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

                        resultados.append(
                            {
                                "data": dt,
                                "funcao": item.get(
                                    "funcao",
                                    ""
                                ),
                                "irmao": nome_irmao
                            }
                        )


            if resultados:

                st.success(
                    f"Encontradas "
                    f"{len(resultados)} designação(ões)."
                )

                for resultado in resultados:

                    data = resultado[
                        "data"
                    ]

                    funcao = resultado[
                        "funcao"
                    ]

                    irmao = resultado[
                        "irmao"
                    ]

                    st.markdown(
                        f"""
                        <div class="info-card">

                            <div style="
                                font-size:17px;
                                font-weight:700;
                                color:#1e3a8a;
                            ">
                                📅 {escape(str(data))}
                            </div>

                            <div style="
                                margin-top:8px;
                                font-weight:600;
                            ">
                                {escape(str(funcao))}
                            </div>

                            <div style="
                                margin-top:4px;
                                color:#374151;
                            ">
                                👤 {escape(str(irmao))}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            else:

                st.warning(
                    "Nenhuma designação localizada "
                    "para este nome."
                )


    # ========================================================
    # ABA 3 — PDF
    # ========================================================

    with tab3:

        st.subheader(
            "📄 Documento Oficial para Impressão"
        )

        st.caption(
            f"Mês selecionado: "
            f"**{obter_mes_nome(mes_selecionado)}**"
        )

        # ----------------------------------------------------
        # Procurar PDF correspondente ao mês
        # ----------------------------------------------------

        nomes_pdf = []

        mes_nome = obter_mes_nome(
            mes_selecionado
        )

        nomes_pdf.append(
            f"Designações_Mecânicas_-_{mes_nome}.pdf"
        )

        nomes_pdf.append(
            f"Designacoes_Mecanicas_-_{mes_nome}.pdf"
        )

        nomes_pdf.append(
            "Designações_Mecânicas_-_Outubro_2026.pdf"
        )

        pdf_encontrado = None

        for nome_pdf in nomes_pdf:

            if os.path.exists(nome_pdf):

                pdf_encontrado = nome_pdf
                break


        if pdf_encontrado:

            with open(
                pdf_encontrado,
                "rb"
            ) as arquivo_pdf:

                st.download_button(
                    label=(
                        "🖨️ Descarregar / "
                        "Imprimir PDF Oficial"
                    ),
                    data=arquivo_pdf.read(),
                    file_name=pdf_encontrado,
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )

        else:

            st.info(
                "O PDF oficial deste mês não foi encontrado "
                "no projeto."
            )


    # ========================================================
    # ABA 4 — ADMINISTRAR ESCALAS
    # ========================================================

    if tab4 is not None:

        with tab4:

            st.subheader(
                "⚙️ Gerir Escalas"
            )

            st.markdown(
                "### ➕ Cadastrar Nova Designação"
            )

            with st.form(
                "form_nova_designacao"
            ):

                c_mes, c_data = st.columns(
                    2
                )

                # --------------------------------------------
                # MÊS
                # --------------------------------------------

                mes_input = c_mes.text_input(
                    "Mês (Ano-Mês):",
                    value=mes_selecionado,
                    help="Exemplo: 2026-10"
                ).strip()


                # --------------------------------------------
                # DATA
                # --------------------------------------------

                data_texto_input = c_data.text_input(
                    "Data da Reunião:",
                    placeholder="Ex.: Segunda-feira — 02/11/2026",
                    help="Use uma data no formato DD/MM/AAAA."
                ).strip()


                c_func, c_irm = st.columns(
                    2
                )


                # --------------------------------------------
                # FUNÇÃO
                # --------------------------------------------

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


                # --------------------------------------------
                # IRMÃO
                # --------------------------------------------

                irmao_input = c_irm.text_input(
                    "Nome do Irmão:"
                ).strip()


                # --------------------------------------------
                # TIPO DE REUNIÃO
                # --------------------------------------------

                dia_sem_input = st.selectbox(
                    "Tipo de Reunião:",
                    [
                        "seg",
                        "sab"
                    ],
                    format_func=lambda x:
                        "Segunda-feira"
                        if x == "seg"
                        else "Sábado"
                )


                # --------------------------------------------
                # BOTÃO
                # --------------------------------------------

                enviar = st.form_submit_button(
                    "➕ Adicionar à Escala",
                    type="primary",
                    use_container_width=True
                )


                if enviar:

                    if (
                        not mes_input
                        or not data_texto_input
                        or not irmao_input
                    ):

                        st.warning(
                            "Preencha todos os campos."
                        )

                    elif not re.match(
                        r"^\d{4}-\d{2}$",
                        mes_input
                    ):

                        st.warning(
                            "O mês deve estar no formato YYYY-MM. "
                            "Exemplo: 2026-11."
                        )

                    elif converter_data(
                        data_texto_input
                    ) is None:

                        st.warning(
                            "A data deve conter uma data válida "
                            "no formato DD/MM/AAAA."
                        )

                    else:

                        try:

                            # --------------------------------
                            # CONFIRMAR DIA DA SEMANA
                            # --------------------------------

                            data_real = converter_data(
                                data_texto_input
                            )

                            dia_calculado = (
                                "sab"
                                if data_real.weekday() == 5
                                else
                                "seg"
                                if data_real.weekday() == 0
                                else
                                None
                            )

                            if dia_calculado is None:

                                st.warning(
                                    "A data informada não é "
                                    "uma segunda-feira ou sábado."
                                )

                            elif (
                                dia_calculado
                                != dia_sem_input
                            ):

                                st.warning(
                                    "O tipo de reunião não corresponde "
                                    "ao dia informado."
                                )

                            else:

                                data_formatada = (
                                    normalizar_data_texto(
                                        data_texto_input,
                                        dia_sem_input
                                    )
                                )

                                # ----------------------------
                                # VERIFICAR DUPLICIDADE
                                # ----------------------------

                                duplicado = (
                                    supabase
                                    .table("escalas")
                                    .select("id")
                                    .eq(
                                        "mes",
                                        mes_input
                                    )
                                    .eq(
                                        "data_texto",
                                        data_formatada
                                    )
                                    .eq(
                                        "funcao",
                                        funcao_input
                                    )
                                    .eq(
                                        "irmao",
                                        irmao_input
                                    )
                                    .execute()
                                )

                                if duplicado.data:

                                    st.warning(
                                        "Essa mesma designação "
                                        "já está cadastrada."
                                    )

                                else:

                                    (
                                        supabase
                                        .table("escalas")
                                        .insert({
                                            "mes": mes_input,
                                            "data_texto": data_formatada,
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

                        except Exception:

                            st.error(
                                "Não foi possível adicionar "
                                "a designação."
                            )


            # =================================================
            # GERENCIAR REGISTROS EXISTENTES
            # =================================================

            st.divider()

            st.markdown(
                "### 📋 Designações cadastradas neste mês"
            )

            if not dados_escala:

                st.info(
                    "Nenhuma designação cadastrada."
                )

            else:

                for item in dados_escala:

                    registro_id = item.get(
                        "id"
                    )

                    data_texto = str(
                        item.get(
                            "data_texto",
                            ""
                        )
                    )

                    funcao = str(
                        item.get(
                            "funcao",
                            ""
                        )
                    )

                    irmao = str(
                        item.get(
                            "irmao",
                            ""
                        )
                    )

                    with st.expander(
                        f"📅 {data_texto} — "
                        f"{funcao} — "
                        f"{irmao}"
                    ):

                        col_edit, col_delete = st.columns(
                            [4, 1]
                        )

                        novo_nome = col_edit.text_input(
                            "Irmão:",
                            value=irmao,
                            key=f"nome_{registro_id}"
                        )

                        if col_edit.button(
                            "💾 Salvar alteração",
                            key=f"salvar_{registro_id}",
                            use_container_width=True
                        ):

                            if not novo_nome.strip():

                                st.warning(
                                    "O nome não pode ficar vazio."
                                )

                            else:

                                try:

                                    (
                                        supabase
                                        .table("escalas")
                                        .update({
                                            "irmao": novo_nome.strip()
                                        })
                                        .eq(
                                            "id",
                                            registro_id
                                        )
                                        .execute()
                                    )

                                    st.success(
                                        "Alteração salva."
                                    )

                                    st.rerun()

                                except Exception:

                                    st.error(
                                        "Não foi possível salvar a alteração."
                                    )


                        if col_delete.button(
                            "🗑️ Excluir",
                            key=f"excluir_{registro_id}",
                            use_container_width=True
                        ):

                            try:

                                (
                                    supabase
                                    .table("escalas")
                                    .delete()
                                    .eq(
                                        "id",
                                        registro_id
                                    )
                                    .execute()
                                )

                                st.success(
                                    "Designação excluída."
                                )

                                st.rerun()

                            except Exception:

                                st.error(
                                    "Não foi possível excluir a designação."
                                )


    # ========================================================
    # PAINEL DO ADMIN — APROVAR UTILIZADORES
    # ========================================================

    if st.session_state["user_role"] == "admin":

        st.sidebar.markdown(
            "---"
        )

        st.sidebar.subheader(
            "⚙️ Aprovar Utilizadores"
        )

        try:

            pendentes = (
                supabase
                .table("usuarios")
                .select(
                    "id,nome,email,telefone,status,perfil"
                )
                .eq(
                    "status",
                    "pendente"
                )
                .execute()
            )

            usuarios_pendentes = (
                pendentes.data or []
            )

            if usuarios_pendentes:

                for u in usuarios_pendentes:

                    st.sidebar.write(
                        f"👤 **{u.get('nome', '')}**"
                    )

                    st.sidebar.caption(
                        f"📧 {u.get('email', '')}"
                    )

                    st.sidebar.caption(
                        f"📱 {u.get('telefone', 'Sem telefone')}"
                    )

                    c_ap, c_rec = (
                        st.sidebar.columns(2)
                    )


                    # ----------------------------------------
                    # APROVAR
                    # ----------------------------------------

                    if c_ap.button(
                        "✅",
                        key=f"ap_{u['id']}",
                        help="Aprovar utilizador"
                    ):

                        try:

                            (
                                supabase
                                .table("usuarios")
                                .update({
                                    "status": "aprovado"
                                })
                                .eq(
                                    "id",
                                    u["id"]
                                )
                                .execute()
                            )

                            st.rerun()

                        except Exception:

                            st.sidebar.error(
                                "Não foi possível aprovar."
                            )


                    # ----------------------------------------
                    # RECUSAR
                    # ----------------------------------------

                    if c_rec.button(
                        "❌",
                        key=f"rec_{u['id']}",
                        help="Recusar utilizador"
                    ):

                        try:

                            (
                                supabase
                                .table("usuarios")
                                .update({
                                    "status": "recusado"
                                })
                                .eq(
                                    "id",
                                    u["id"]
                                )
                                .execute()
                            )

                            st.rerun()

                        except Exception:

                            st.sidebar.error(
                                "Não foi possível recusar."
                            )

                    st.sidebar.markdown(
                        "---"
                    )

            else:

                st.sidebar.caption(
                    "Nenhum utilizador pendente."
                )

        except Exception:

            st.sidebar.error(
                "Não foi possível carregar os utilizadores pendentes."
            )
