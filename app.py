import os
import re
import html
import hashlib
import hmac
import secrets
from datetime import date, datetime

import streamlit as st
from supabase import create_client, Client


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Designações Mecânicas — Congregação Jardim América",
    page_icon="🏛️",
    layout="wide"
)


# ============================================================
# CONFIGURAÇÃO DO SUPABASE
# ============================================================
#
# RECOMENDADO:
#
# .streamlit/secrets.toml
#
# SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
# SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp3c3RnaW56dWltcmJ2dmF2cmx2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA2MjIwNDgsImV4cCI6MjEwNjE5ODA0OH0.XNLaxpWCElIntlXWS6_moHHCnzkTXUXBhcFoRx6K93M"
#
# Também funciona com variáveis de ambiente.
# ============================================================

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

except Exception:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")


if not SUPABASE_URL or not SUPABASE_KEY:
    st.error(
        "As configurações do Supabase não foram encontradas."
    )

    st.info(
        "Configure SUPABASE_URL e SUPABASE_KEY nos Secrets "
        "do Streamlit."
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
        "Não foi possível conectar ao banco de dados."
    )
    st.stop()


# ============================================================
# CONSTANTES
# ============================================================

STATUS_APROVADO = "aprovado"
STATUS_PENDENTE = "pendente"
STATUS_RECUSADO = "recusado"

PERFIL_ADMIN = "admin"
PERFIL_IRMAO = "irmao"

DIAS_REUNIAO = {
    "seg": "Segunda-feira",
    "sab": "Sábado"
}

FUNCOES = [
    "🗣️ Oração Inicial",
    "🗣️ Oração Final",
    "📖 Leitor A Sentinela",
    "🎤 Microfones",
    "🚪 Ind. Entrada",
    "🏛️ Ind. Auditório"
]


# ============================================================
# ESTADO DA SESSÃO
# ============================================================

DEFAULT_SESSION = {
    "logged_in": False,
    "user_id": None,
    "user_name": "",
    "user_email": "",
    "user_role": None,
}


for key, value in DEFAULT_SESSION.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# FUNÇÕES DE SEGURANÇA
# ============================================================

def hash_password(password: str) -> str:
    """
    Gera hash PBKDF2 usando SHA-256.

    Formato armazenado:
    pbkdf2_sha256$iterations$salt$hash
    """

    iterations = 310_000

    salt = secrets.token_hex(16)

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations
    )

    encoded_hash = derived_key.hex()

    return (
        f"pbkdf2_sha256$"
        f"{iterations}$"
        f"{salt}$"
        f"{encoded_hash}"
    )


def verify_password(
    password: str,
    stored_password: str
) -> bool:
    """
    Verifica senha nova com hash PBKDF2.

    Também reconhece senhas antigas armazenadas
    em texto puro para permitir migração automática.
    """

    if not stored_password:
        return False

    # --------------------------------------------------------
    # SENHA NOVA — HASH
    # --------------------------------------------------------

    if stored_password.startswith("pbkdf2_sha256$"):

        try:

            parts = stored_password.split("$")

            if len(parts) != 4:
                return False

            _, iterations_text, salt, stored_hash = parts

            iterations = int(iterations_text)

            derived_key = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                iterations
            )

            calculated_hash = derived_key.hex()

            return hmac.compare_digest(
                calculated_hash,
                stored_hash
            )

        except Exception:
            return False

    # --------------------------------------------------------
    # SENHA ANTIGA — TEXTO PURO
    # --------------------------------------------------------

    return hmac.compare_digest(
        password,
        stored_password
    )


def is_legacy_password(stored_password: str) -> bool:
    return not stored_password.startswith(
        "pbkdf2_sha256$"
    )


# ============================================================
# FUNÇÕES DE VALIDAÇÃO
# ============================================================

def validar_email(email: str) -> bool:

    pattern = (
        r"^[A-Za-z0-9._%+-]+@"
        r"[A-Za-z0-9.-]+\."
        r"[A-Za-z]{2,}$"
    )

    return bool(
        re.match(pattern, email)
    )


def validar_mes(mes: str) -> bool:

    if not re.match(
        r"^\d{4}-(0[1-9]|1[0-2])$",
        mes
    ):
        return False

    try:
        datetime.strptime(
            mes,
            "%Y-%m"
        )
        return True

    except ValueError:
        return False


def formatar_data_reuniao(
    data_reuniao: date
) -> tuple[str, str]:
    """
    Retorna:
        data_texto
        dia_semana
    """

    weekday = data_reuniao.weekday()

    if weekday == 0:
        dia_semana = "seg"

    elif weekday == 5:
        dia_semana = "sab"

    else:
        dia_semana = ""

    nomes = {
        "seg": "Segunda-feira",
        "sab": "Sábado"
    }

    nome_dia = nomes.get(
        dia_semana,
        data_reuniao.strftime("%A")
    )

    data_texto = (
        f"{nome_dia} — "
        f"{data_reuniao.strftime('%d/%m/%Y')}"
    )

    return data_texto, dia_semana


def extrair_data(data_texto: str):
    """
    Tenta extrair uma data dd/mm/yyyy
    do campo data_texto.
    """

    match = re.search(
        r"(\d{2})/(\d{2})/(\d{4})",
        data_texto
    )

    if not match:
        return None

    dia, mes, ano = match.groups()

    try:

        return date(
            int(ano),
            int(mes),
            int(dia)
        )

    except ValueError:
        return None


# ============================================================
# FUNÇÕES DE BANCO
# ============================================================

def buscar_usuario_por_email(email: str):

    response = (
        supabase
        .table("usuarios")
        .select(
            "id,nome,email,telefone,senha,status,perfil"
        )
        .eq("email", email)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


def buscar_usuario_por_id(user_id):

    response = (
        supabase
        .table("usuarios")
        .select(
            "id,nome,email,telefone,status,perfil"
        )
        .eq("id", user_id)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


def limpar_sessao():

    for key, value in DEFAULT_SESSION.items():
        st.session_state[key] = value


def realizar_login(user):

    st.session_state["logged_in"] = True
    st.session_state["user_id"] = user["id"]
    st.session_state["user_name"] = user.get(
        "nome",
        ""
    )
    st.session_state["user_email"] = user.get(
        "email",
        ""
    )
    st.session_state["user_role"] = user.get(
        "perfil",
        PERFIL_IRMAO
    )


def obter_meses():

    response = (
        supabase
        .table("escalas")
        .select("mes")
        .execute()
    )

    meses = set()

    for item in response.data or []:

        mes = str(
            item.get("mes", "")
        ).strip()

        if validar_mes(mes):
            meses.add(mes)

    return sorted(
        meses,
        reverse=True
    )


def buscar_escalas(mes):

    response = (
        supabase
        .table("escalas")
        .select(
            "id,mes,data_texto,dia_semana,funcao,irmao"
        )
        .eq("mes", mes)
        .execute()
    )

    return response.data or []


def organizar_escalas(dados):

    grupos = {}

    for item in dados:

        data_texto = str(
            item.get(
                "data_texto",
                "Data não informada"
            )
        )

        if data_texto not in grupos:
            grupos[data_texto] = {
                "data_texto": data_texto,
                "dia_semana": item.get(
                    "dia_semana",
                    ""
                ),
                "itens": []
            }

        grupos[data_texto]["itens"].append(
            item
        )

    def chave_ordenacao(grupo):

        data = extrair_data(
            grupo["data_texto"]
        )

        if data:
            return data

        return date.max

    grupos_ordenados = sorted(
        grupos.values(),
        key=chave_ordenacao
    )

    return grupos_ordenados


def designacao_duplicada(
    mes,
    data_texto,
    funcao,
    irmao,
    ignorar_id=None
):

    response = (
        supabase
        .table("escalas")
        .select("id")
        .eq("mes", mes)
        .eq("data_texto", data_texto)
        .eq("funcao", funcao)
        .eq("irmao", irmao)
        .execute()
    )

    for item in response.data or []:

        if ignorar_id is None:
            return True

        if str(item["id"]) != str(
            ignorar_id
        ):
            return True

    return False


# ============================================================
# TELA DE LOGIN
# ============================================================

if not st.session_state["logged_in"]:

    st.markdown(
        """
        <div style="
            text-align:center;
            padding:25px;
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
                "E-mail:",
                key="login_email"
            ).strip().lower()

            senha_login = st.text_input(
                "Senha:",
                type="password",
                key="login_senha"
            )

            if st.button(
                "Entrar no Portal",
                type="primary",
                use_container_width=True
            ):

                if not email_login or not senha_login:

                    st.warning(
                        "Preencha o e-mail e a senha."
                    )

                elif not validar_email(
                    email_login
                ):

                    st.warning(
                        "Digite um e-mail válido."
                    )

                else:

                    try:

                        user = buscar_usuario_por_email(
                            email_login
                        )

                        if not user:

                            st.error(
                                "E-mail ou senha incorretos."
                            )

                        elif not verify_password(
                            senha_login,
                            user.get("senha", "")
                        ):

                            st.error(
                                "E-mail ou senha incorretos."
                            )

                        elif user.get("status") == STATUS_PENDENTE:

                            st.warning(
                                "⏳ Seu cadastro ainda "
                                "está aguardando aprovação."
                            )

                        elif user.get("status") != STATUS_APROVADO:

                            st.error(
                                "❌ Seu acesso não está aprovado."
                            )

                        else:

                            # --------------------------------
                            # MIGRAÇÃO AUTOMÁTICA
                            # --------------------------------
                            #
                            # Se a conta ainda tiver senha
                            # antiga em texto puro, ela será
                            # convertida para hash.
                            # --------------------------------

                            if is_legacy_password(
                                user.get("senha", "")
                            ):

                                try:

                                    supabase.table(
                                        "usuarios"
                                    ).update({
                                        "senha": hash_password(
                                            senha_login
                                        )
                                    }).eq(
                                        "id",
                                        user["id"]
                                    ).execute()

                                except Exception:
                                    pass

                            realizar_login(user)

                            st.rerun()

                    except Exception:

                        st.error(
                            "Não foi possível verificar "
                            "a conta agora."
                        )


        # ====================================================
        # CADASTRO
        # ====================================================

        with tab_cadastro:

            st.subheader(
                "Cadastro de Novo Irmão"
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
                "Crie uma senha:",
                type="password"
            )

            confirmar_senha = st.text_input(
                "Confirme a senha:",
                type="password"
            )

            if st.button(
                "Enviar Pedido de Cadastro",
                use_container_width=True
            ):

                if not nome_cad:

                    st.warning(
                        "Informe seu nome completo."
                    )

                elif len(nome_cad) < 3:

                    st.warning(
                        "Informe um nome válido."
                    )

                elif not email_cad:

                    st.warning(
                        "Informe seu e-mail."
                    )

                elif not validar_email(
                    email_cad
                ):

                    st.warning(
                        "Digite um e-mail válido."
                    )

                elif not tel_cad:

                    st.warning(
                        "Informe seu WhatsApp."
                    )

                elif len(senha_cad) < 8:

                    st.warning(
                        "A senha deve ter pelo menos "
                        "8 caracteres."
                    )

                elif senha_cad != confirmar_senha:

                    st.warning(
                        "As senhas não coincidem."
                    )

                else:

                    try:

                        existing = (
                            supabase
                            .table("usuarios")
                            .select("id")
                            .eq("email", email_cad)
                            .limit(1)
                            .execute()
                        )

                        if existing.data:

                            st.error(
                                "Este e-mail já está "
                                "cadastrado."
                            )

                        else:

                            supabase.table(
                                "usuarios"
                            ).insert({
                                "nome": nome_cad,
                                "email": email_cad,
                                "telefone": tel_cad,
                                "senha": hash_password(
                                    senha_cad
                                ),
                                "status": STATUS_PENDENTE,
                                "perfil": PERFIL_IRMAO
                            }).execute()

                            st.success(
                                "✅ Cadastro enviado! "
                                "Aguarde a aprovação."
                            )

                    except Exception:

                        st.error(
                            "Não foi possível concluir "
                            "o cadastro."
                        )

    st.stop()


# ============================================================
# ÁREA INTERNA
# ============================================================

# ------------------------------------------------------------
# Validar sessão
# ------------------------------------------------------------

if not st.session_state.get(
    "user_id"
):

    limpar_sessao()
    st.rerun()


try:

    usuario_atual = buscar_usuario_por_id(
        st.session_state["user_id"]
    )

except Exception:

    usuario_atual = None


if not usuario_atual:

    limpar_sessao()

    st.error(
        "Sua sessão não pôde ser validada."
    )

    st.stop()


if usuario_atual.get(
    "status"
) != STATUS_APROVADO:

    limpar_sessao()

    st.warning(
        "Seu acesso não está mais aprovado."
    )

    st.stop()


# Atualiza dados básicos da sessão

st.session_state["user_name"] = usuario_atual.get(
    "nome",
    ""
)

st.session_state["user_email"] = usuario_atual.get(
    "email",
    ""
)

st.session_state["user_role"] = usuario_atual.get(
    "perfil",
    PERFIL_IRMAO
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "🏛️ Jardim América"
)

st.sidebar.write(
    f"👤 **{st.session_state['user_name']}**"
)

perfil_exibicao = (
    "Administrador"
    if st.session_state["user_role"] == PERFIL_ADMIN
    else "Irmão"
)

st.sidebar.caption(
    f"Perfil: **{perfil_exibicao}**"
)

if st.sidebar.button(
    "🚪 Terminar Sessão",
    use_container_width=True
):

    limpar_sessao()
    st.rerun()


# ============================================================
# BUSCAR MESES
# ============================================================

try:

    meses_disponiveis = obter_meses()

except Exception:

    meses_disponiveis = []

    st.sidebar.error(
        "Não foi possível carregar os meses."
    )


# ============================================================
# SE NÃO HOUVER MÊS
# ============================================================

if not meses_disponiveis:

    hoje = date.today()

    meses_disponiveis = [
        hoje.strftime("%Y-%m")
    ]


# ============================================================
# SELECIONAR MÊS
# ============================================================

mes_selecionado = st.sidebar.selectbox(
    "📅 Selecionar Mês:",
    meses_disponiveis,
    index=0
)


# ============================================================
# BUSCAR ESCALA
# ============================================================

try:

    dados_escala = buscar_escalas(
        mes_selecionado
    )

except Exception:

    dados_escala = []

    st.error(
        "Não foi possível carregar a escala."
    )


grupos_datas = organizar_escalas(
    dados_escala
)


# ============================================================
# ABAS
# ============================================================

if st.session_state["user_role"] == PERFIL_ADMIN:

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
            "🔍 Minhas Designações",
            "📄 Imprimir PDF"
        ]
    )

    tab4 = None


# ============================================================
# FUNÇÃO PARA RENDERIZAR CARTÃO
# ============================================================

def renderizar_cartao(grupo):

    dia_semana = grupo.get(
        "dia_semana",
        ""
    )

    if dia_semana == "seg":

        cor = "#1e3a8a"
        icone = "🔹"

    elif dia_semana == "sab":

        cor = "#7e22ce"
        icone = "🟣"

    else:

        cor = "#374151"
        icone = "📅"

    data_texto = html.escape(
        str(
            grupo.get(
                "data_texto",
                "Data não informada"
            )
        )
    )

    html_card = f"""
    <div style="
        background:#ffffff;
        border-radius:15px;
        padding:20px;
        margin-bottom:20px;
        border-left:6px solid {cor};
        box-shadow:
            0 3px 10px
            rgba(0,0,0,0.10);
    ">

        <h3 style="
            margin:0 0 18px 0;
            color:{cor};
            font-size:18px;
        ">
            {icone} {data_texto}
        </h3>
    """

    for item in grupo["itens"]:

        funcao = html.escape(
            str(
                item.get(
                    "funcao",
                    ""
                )
            )
        )

        irmao = html.escape(
            str(
                item.get(
                    "irmao",
                    ""
                )
            )
        )

        html_card += f"""
        <div style="
            margin-bottom:12px;
        ">

            <strong style="
                color:#111827;
            ">
                {funcao}
            </strong>

            <br>

            <span style="
                color:#374151;
                font-size:16px;
            ">
                {irmao}
            </span>

        </div>
        """

    html_card += """
    </div>
    """

    st.markdown(
        html_card,
        unsafe_allow_html=True
    )


# ============================================================
# ABA 1 — ESCALA DO MÊS
# ============================================================

with tab1:

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
            box-shadow:
                0 4px 12px
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
                📅 {html.escape(mes_selecionado)}
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )


    if not grupos_datas:

        st.info(
            "Nenhuma escala registrada "
            "para este mês."
        )

    else:

        # ----------------------------------------------------
        # Mostra duas reuniões por linha.
        #
        # A ordem agora vem da DATA real,
        # e a cor vem de dia_semana.
        # ----------------------------------------------------

        for i in range(
            0,
            len(grupos_datas),
            2
        ):

            col1, col2 = st.columns(2)

            with col1:
                renderizar_cartao(
                    grupos_datas[i]
                )

            if i + 1 < len(grupos_datas):

                with col2:

                    renderizar_cartao(
                        grupos_datas[i + 1]
                    )


# ============================================================
# ABA 2 — PROCURAR / MINHAS DESIGNAÇÕES
# ============================================================

with tab2:

    eh_admin = (
        st.session_state["user_role"]
        == PERFIL_ADMIN
    )

    if eh_admin:

        st.subheader(
            "🔍 Consultar Designações"
        )

        busca = st.text_input(
            "Digite o nome do irmão:",
            placeholder="Ex.: João"
        ).strip()

    else:

        st.subheader(
            "🔍 Minhas Designações"
        )

        busca = st.text_input(
            "Nome do irmão:",
            value=st.session_state[
                "user_name"
            ],
            disabled=True
        ).strip()


    if busca:

        encontrados = []

        for grupo in grupos_datas:

            for item in grupo["itens"]:

                nome_irmao = str(
                    item.get(
                        "irmao",
                        ""
                    )
                )

                if busca.lower() in nome_irmao.lower():

                    encontrados.append({
                        "data": grupo[
                            "data_texto"
                        ],
                        "funcao": item.get(
                            "funcao",
                            ""
                        ),
                        "irmao": nome_irmao
                    })


        if encontrados:

            for item in encontrados:

                st.success(
                    f"📅 **{item['data']}** — "
                    f"**{item['funcao']}** — "
                    f"{item['irmao']}"
                )

        else:

            st.warning(
                "Nenhuma designação encontrada."
            )


# ============================================================
# ABA 3 — PDF
# ============================================================

with tab3:

    st.subheader(
        "📄 Documento para Impressão"
    )

    st.info(
        "O sistema procura o PDF correspondente "
        "ao mês selecionado."
    )

    # --------------------------------------------------------
    # Possíveis nomes de arquivo
    # --------------------------------------------------------

    nomes_pdf = [
        f"Designações_Mecânicas_-_{mes_selecionado}.pdf",
        f"Designacoes_Mecanicas_-_{mes_selecionado}.pdf",
        f"Designações_Mecânicas_{mes_selecionado}.pdf",
        f"Designacoes_Mecanicas_{mes_selecionado}.pdf",
    ]

    pdf_encontrado = None

    for nome_pdf in nomes_pdf:

        if os.path.exists(nome_pdf):

            pdf_encontrado = nome_pdf
            break


    if pdf_encontrado:

        with open(
            pdf_encontrado,
            "rb"
        ) as arquivo:

            st.download_button(
                label=(
                    "🖨️ Descarregar / "
                    "Imprimir PDF"
                ),
                data=arquivo.read(),
                file_name=pdf_encontrado,
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )

    else:

        st.warning(
            f"Não foi encontrado um PDF para "
            f"{mes_selecionado}."
        )

        st.caption(
            "O PDF precisa estar no mesmo diretório "
            "da aplicação e seguir um dos nomes "
            "esperados pelo sistema."
        )


# ============================================================
# ABA 4 — ADMINISTRAR ESCALAS
# ============================================================

if tab4 is not None:

    with tab4:

        st.subheader(
            "⚙️ Gerenciar Escalas"
        )

        # ====================================================
        # CADASTRAR
        # ====================================================

        st.markdown(
            "### ➕ Nova Designação"
        )

        with st.form(
            "form_nova_designacao"
        ):

            c1, c2 = st.columns(2)

            with c1:

                data_input = st.date_input(
                    "Data da reunião:",
                    value=date.today()
                )

            with c2:

                funcao_input = st.selectbox(
                    "Função:",
                    FUNCOES
                )


            irmao_input = st.text_input(
                "Nome do Irmão:"
            ).strip()


            enviar = st.form_submit_button(
                "➕ Adicionar à Escala",
                type="primary",
                use_container_width=True
            )


            if enviar:

                data_texto, dia_semana = (
                    formatar_data_reuniao(
                        data_input
                    )
                )

                mes_input = data_input.strftime(
                    "%Y-%m"
                )


                if dia_semana not in (
                    "seg",
                    "sab"
                ):

                    st.error(
                        "A data escolhida não é "
                        "segunda-feira nem sábado."
                    )

                elif not irmao_input:

                    st.warning(
                        "Informe o nome do irmão."
                    )

                elif len(irmao_input) < 2:

                    st.warning(
                        "Informe um nome válido."
                    )

                elif designacao_duplicada(
                    mes_input,
                    data_texto,
                    funcao_input,
                    irmao_input
                ):

                    st.error(
                        "Essa mesma designação já "
                        "está cadastrada."
                    )

                else:

                    try:

                        supabase.table(
                            "escalas"
                        ).insert({
                            "mes": mes_input,
                            "data_texto": data_texto,
                            "dia_semana": dia_semana,
                            "funcao": funcao_input,
                            "irmao": irmao_input
                        }).execute()

                        st.success(
                            "✅ Designação adicionada!"
                        )

                        st.rerun()

                    except Exception:

                        st.error(
                            "Não foi possível adicionar "
                            "a designação."
                        )


        st.divider()


        # ====================================================
        # EDITAR / EXCLUIR
        # ====================================================

        st.markdown(
            "### ✏️ Editar ou Excluir Designação"
        )

        if not dados_escala:

            st.info(
                "Não há designações neste mês."
            )

        else:

            opcoes = {}

            for item in dados_escala:

                item_id = str(
                    item["id"]
                )

                descricao = (
                    f"{item.get('data_texto', '')} | "
                    f"{item.get('funcao', '')} | "
                    f"{item.get('irmao', '')}"
                )

                opcoes[
                    item_id
                ] = descricao


            id_selecionado = st.selectbox(
                "Selecione uma designação:",
                list(opcoes.keys()),
                format_func=lambda x:
                    opcoes[x]
            )


            item_atual = next(
                (
                    item
                    for item in dados_escala
                    if str(item["id"])
                    == str(id_selecionado)
                ),
                None
            )


            if item_atual:

                with st.form(
                    "form_editar_designacao"
                ):

                    data_existente = (
                        extrair_data(
                            item_atual.get(
                                "data_texto",
                                ""
                            )
                        )
                    )

                    if not data_existente:

                        data_existente = date.today()


                    nova_data = st.date_input(
                        "Data:",
                        value=data_existente,
                        key=f"data_edit_{id_selecionado}"
                    )


                    funcoes_edit = FUNCOES.copy()

                    funcao_existente = item_atual.get(
                        "funcao",
                        ""
                    )

                    if (
                        funcao_existente
                        and funcao_existente
                        not in funcoes_edit
                    ):

                        funcoes_edit.insert(
                            0,
                            funcao_existente
                        )


                    nova_funcao = st.selectbox(
                        "Função:",
                        funcoes_edit,
                        index=funcoes_edit.index(
                            funcao_existente
                        ),
                        key=f"funcao_edit_{id_selecionado}"
                    )


                    novo_irmao = st.text_input(
                        "Nome do Irmão:",
                        value=item_atual.get(
                            "irmao",
                            ""
                        ),
                        key=f"irmao_edit_{id_selecionado}"
                    ).strip()


                    c_salvar, c_excluir = st.columns(2)


                    salvar = c_salvar.form_submit_button(
                        "💾 Salvar Alterações",
                        type="primary",
                        use_container_width=True
                    )


                    excluir = c_excluir.form_submit_button(
                        "🗑️ Excluir",
                        use_container_width=True
                    )


                    # ========================================
                    # EXCLUIR
                    # ========================================

                    if excluir:

                        try:

                            (
                                supabase
                                .table("escalas")
                                .delete()
                                .eq(
                                    "id",
                                    id_selecionado
                                )
                                .execute()
                            )

                            st.success(
                                "Designação excluída."
                            )

                            st.rerun()

                        except Exception:

                            st.error(
                                "Não foi possível excluir "
                                "a designação."
                            )


                    # ========================================
                    # SALVAR
                    # ========================================

                    if salvar:

                        data_texto_edit, dia_edit = (
                            formatar_data_reuniao(
                                nova_data
                            )
                        )

                        mes_edit = (
                            nova_data.strftime(
                                "%Y-%m"
                            )
                        )


                        if dia_edit not in (
                            "seg",
                            "sab"
                        ):

                            st.error(
                                "A data deve ser "
                                "segunda-feira ou sábado."
                            )

                        elif not novo_irmao:

                            st.warning(
                                "Informe o nome do irmão."
                            )

                        elif designacao_duplicada(
                            mes_edit,
                            data_texto_edit,
                            nova_funcao,
                            novo_irmao,
                            ignorar_id=id_selecionado
                        ):

                            st.error(
                                "Já existe uma designação "
                                "igual para essa reunião."
                            )

                        else:

                            try:

                                (
                                    supabase
                                    .table("escalas")
                                    .update({
                                        "mes": mes_edit,
                                        "data_texto":
                                            data_texto_edit,
                                        "dia_semana":
                                            dia_edit,
                                        "funcao":
                                            nova_funcao,
                                        "irmao":
                                            novo_irmao
                                    })
                                    .eq(
                                        "id",
                                        id_selecionado
                                    )
                                    .execute()
                                )

                                st.success(
                                    "✅ Alterações salvas!"
                                )

                                st.rerun()

                            except Exception:

                                st.error(
                                    "Não foi possível salvar "
                                    "as alterações."
                                )


# ============================================================
# PAINEL ADMIN — USUÁRIOS PENDENTES
# ============================================================

if st.session_state["user_role"] == PERFIL_ADMIN:

    st.sidebar.divider()

    st.sidebar.subheader(
        "⚙️ Aprovar Usuários"
    )

    try:

        pendentes = (
            supabase
            .table("usuarios")
            .select(
                "id,nome,email,telefone,status"
            )
            .eq(
                "status",
                STATUS_PENDENTE
            )
            .execute()
        )

        usuarios_pendentes = (
            pendentes.data or []
        )


        if usuarios_pendentes:

            for usuario in usuarios_pendentes:

                nome = html.escape(
                    str(
                        usuario.get(
                            "nome",
                            ""
                        )
                    )
                )

                telefone = html.escape(
                    str(
                        usuario.get(
                            "telefone",
                            "Sem telefone"
                        )
                    )
                )

                email = html.escape(
                    str(
                        usuario.get(
                            "email",
                            ""
                        )
                    )
                )


                st.sidebar.markdown(
                    f"""
                    **👤 {nome}**

                    {email}

                    📱 {telefone}
                    """,
                    unsafe_allow_html=True
                )


                c_ap, c_rec = (
                    st.sidebar.columns(2)
                )


                # --------------------------------------------
                # APROVAR
                # --------------------------------------------

                if c_ap.button(
                    "✅ Aprovar",
                    key=f"aprovar_{usuario['id']}"
                ):

                    try:

                        (
                            supabase
                            .table("usuarios")
                            .update({
                                "status":
                                    STATUS_APROVADO
                            })
                            .eq(
                                "id",
                                usuario["id"]
                            )
                            .execute()
                        )

                        st.rerun()

                    except Exception:

                        st.sidebar.error(
                            "Não foi possível aprovar."
                        )


                # --------------------------------------------
                # RECUSAR
                # --------------------------------------------

                if c_rec.button(
                    "❌ Recusar",
                    key=f"recusar_{usuario['id']}"
                ):

                    try:

                        (
                            supabase
                            .table("usuarios")
                            .update({
                                "status":
                                    STATUS_RECUSADO
                            })
                            .eq(
                                "id",
                                usuario["id"]
                            )
                            .execute()
                        )

                        st.rerun()

                    except Exception:

                        st.sidebar.error(
                            "Não foi possível recusar."
                        )

        else:

            st.sidebar.caption(
                "Nenhum usuário pendente."
            )


    except Exception:

        st.sidebar.error(
            "Não foi possível carregar "
            "os usuários pendentes."
        )


# ============================================================
# RODAPÉ
# ============================================================

st.markdown(
    """
    <div style="
        text-align:center;
        color:#9CA3AF;
        padding:25px 0 10px 0;
        font-size:13px;
    ">
        Portal de Designações Mecânicas
        — Congregação Jardim América
    </div>
    """,
    unsafe_allow_html=True
)
```
