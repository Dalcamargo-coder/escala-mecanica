import os
import re
import hashlib
import secrets
from datetime import datetime, date
from typing import Optional, Tuple

import streamlit as st
from supabase import create_client, Client


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Designações Mecânicas",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CONFIGURAÇÃO DO SUPABASE
# ============================================================

def obter_config_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        st.error(
            "As configurações do Supabase não foram encontradas. "
            "Configure SUPABASE_URL e SUPABASE_KEY."
        )
        st.stop()

    return url, key


SUPABASE_URL, SUPABASE_KEY = obter_config_supabase()


@st.cache_resource
def criar_cliente_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = criar_cliente_supabase()


# ============================================================
# ESTILO
# ============================================================

st.markdown(
    """
    <style>
        .main {
            padding-top: 1rem;
        }

        .titulo-principal {
            text-align: center;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        .subtitulo {
            text-align: center;
            color: #666;
            margin-bottom: 1.5rem;
        }

        .card {
            padding: 1.2rem;
            border-radius: 12px;
            border: 1px solid #ddd;
            margin-bottom: 1rem;
            background: white;
        }

        .segunda-feira {
            border-left: 6px solid #4CAF50;
        }

        .sabado {
            border-left: 6px solid #2196F3;
        }

        .nome-irmao {
            font-weight: 700;
            font-size: 1.05rem;
        }

        .funcao {
            color: #555;
            margin-top: 4px;
        }

        .data-escala {
            font-weight: 700;
            margin-bottom: 0.7rem;
        }

        .status-pendente {
            padding: 8px;
            border-radius: 8px;
            background: #fff3cd;
            color: #856404;
        }

        .status-aprovado {
            padding: 8px;
            border-radius: 8px;
            background: #d4edda;
            color: #155724;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CONSTANTES
# ============================================================

FUNCOES = [
    "🗣️ Oração Inicial",
    "🗣️ Oração Final",
    "📖 Leitor A Sentinela",
    "🎤 Microfones",
    "🚪 Ind. Entrada",
    "🏛️ Ind. Auditório",
]

DIAS_REUNIAO = {
    "seg": "Segunda-feira",
    "sab": "Sábado",
}


# ============================================================
# SESSION STATE
# ============================================================

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "logado" not in st.session_state:
    st.session_state.logado = False


# ============================================================
# FUNÇÕES DE SEGURANÇA
# ============================================================

def gerar_hash_senha(senha: str) -> str:
    """
    Gera hash PBKDF2-SHA256 para armazenar a senha.
    """
    salt = secrets.token_bytes(16)

    chave = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        salt,
        120000,
    )

    return (
        "pbkdf2_sha256$120000$"
        + salt.hex()
        + "$"
        + chave.hex()
    )


def verificar_senha(senha: str, senha_salva: str) -> bool:
    """
    Verifica senha nova com hash PBKDF2.
    Também aceita temporariamente senha antiga em texto puro
    para permitir migração.
    """

    if not senha_salva:
        return False

    if senha_salva.startswith("pbkdf2_sha256$"):
        try:
            partes = senha_salva.split("$")

            if len(partes) != 4:
                return False

            _, iteracoes, salt_hex, hash_hex = partes

            iteracoes = int(iteracoes)

            salt = bytes.fromhex(salt_hex)
            hash_esperado = bytes.fromhex(hash_hex)

            hash_atual = hashlib.pbkdf2_hmac(
                "sha256",
                senha.encode("utf-8"),
                salt,
                iteracoes,
            )

            return secrets.compare_digest(
                hash_atual,
                hash_esperado,
            )

        except Exception:
            return False

    # Compatibilidade com senhas antigas
    return secrets.compare_digest(
        senha,
        senha_salva,
    )


# ============================================================
# VALIDAÇÕES
# ============================================================

def email_valido(email: str) -> bool:
    padrao = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(padrao, email))


def nome_valido(nome: str) -> bool:
    nome = nome.strip()

    if len(nome) < 3:
        return False

    return True


def senha_valida(senha: str) -> bool:
    return len(senha) >= 6


def obter_data(data_texto: str) -> Optional[date]:
    formatos = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
    ]

    for formato in formatos:
        try:
            return datetime.strptime(
                data_texto.strip(),
                formato,
            ).date()
        except ValueError:
            pass

    return None


def normalizar_data(data_input) -> Optional[date]:
    if isinstance(data_input, datetime):
        return data_input.date()

    if isinstance(data_input, date):
        return data_input

    if isinstance(data_input, str):
        return obter_data(data_input)

    return None


# ============================================================
# FUNÇÕES DE USUÁRIO
# ============================================================

def buscar_usuario_por_email(email: str):
    try:
        resposta = (
            supabase
            .table("usuarios")
            .select(
                "id,nome,email,senha,telefone,status,perfil"
            )
            .eq("email", email.strip().lower())
            .limit(1)
            .execute()
        )

        if resposta.data:
            return resposta.data[0]

    except Exception:
        return None

    return None


def cadastrar_usuario(
    nome: str,
    email: str,
    senha: str,
    telefone: str,
):
    nome = nome.strip()
    email = email.strip().lower()
    telefone = telefone.strip()

    if not nome_valido(nome):
        return False, "Digite um nome válido."

    if not email_valido(email):
        return False, "Digite um e-mail válido."

    if not senha_valida(senha):
        return False, "A senha deve ter pelo menos 6 caracteres."

    existente = buscar_usuario_por_email(email)

    if existente:
        return False, "Este e-mail já está cadastrado."

    senha_hash = gerar_hash_senha(senha)

    dados = {
        "nome": nome,
        "email": email,
        "senha": senha_hash,
        "telefone": telefone,
        "status": "pendente",
        "perfil": "usuario",
    }

    try:
        supabase.table("usuarios").insert(dados).execute()

        return (
            True,
            "Cadastro realizado. Aguarde a aprovação do administrador.",
        )

    except Exception:
        return False, "Não foi possível realizar o cadastro."


def autenticar_usuario(
    email: str,
    senha: str,
) -> Tuple[bool, Optional[dict], str]:

    email = email.strip().lower()

    if not email_valido(email):
        return False, None, "E-mail ou senha inválidos."

    usuario = buscar_usuario_por_email(email)

    if not usuario:
        return False, None, "E-mail ou senha inválidos."

    if not verificar_senha(
        senha,
        usuario.get("senha", ""),
    ):
        return False, None, "E-mail ou senha inválidos."

    status = str(
        usuario.get("status", "")
    ).lower().strip()

    if status == "pendente":
        return (
            False,
            None,
            "Seu cadastro ainda está aguardando aprovação.",
        )

    if status in ("bloqueado", "rejeitado", "inativo"):
        return (
            False,
            None,
            "Seu cadastro não está autorizado.",
        )

    # Migração automática de senha antiga
    senha_atual = usuario.get("senha", "")

    if not senha_atual.startswith("pbkdf2_sha256$"):
        try:
            nova_senha = gerar_hash_senha(senha)

            supabase.table("usuarios").update(
                {"senha": nova_senha}
            ).eq(
                "id",
                usuario["id"],
            ).execute()

        except Exception:
            pass

    return True, usuario, ""


def usuario_e_admin() -> bool:
    usuario = st.session_state.get("usuario")

    if not usuario:
        return False

    perfil = str(
        usuario.get("perfil", "")
    ).lower().strip()

    return perfil in (
        "admin",
        "administrador",
    )


def fazer_logout():
    st.session_state.usuario = None
    st.session_state.logado = False
    st.rerun()


# ============================================================
# FUNÇÕES DE ESCALAS
# ============================================================

def buscar_meses():
    try:
        resposta = (
            supabase
            .table("escalas")
            .select("mes")
            .execute()
        )

        meses = []

        for item in resposta.data or []:
            mes = item.get("mes")

            if mes and mes not in meses:
                meses.append(mes)

        return sorted(meses)

    except Exception:
        return []


def buscar_escala(mes: str):
    try:
        resposta = (
            supabase
            .table("escalas")
            .select(
                "id,mes,data_texto,dia_semana,funcao,irmao"
            )
            .eq("mes", mes)
            .execute()
        )

        dados = resposta.data or []

        def chave_ordenacao(item):
            data = obter_data(
                str(item.get("data_texto", ""))
            )

            if data:
                return (
                    data,
                    str(item.get("funcao", "")),
                    str(item.get("irmao", "")),
                )

            return (
                date.max,
                str(item.get("funcao", "")),
                str(item.get("irmao", "")),
            )

        dados.sort(key=chave_ordenacao)

        return dados

    except Exception:
        return []


def verificar_duplicidade(
    mes: str,
    data_texto: str,
    funcao: str,
    ignorar_id=None,
) -> bool:

    try:
        consulta = (
            supabase
            .table("escalas")
            .select("id")
            .eq("mes", mes)
            .eq("data_texto", data_texto)
            .eq("funcao", funcao)
        )

        if ignorar_id is not None:
            consulta = consulta.neq(
                "id",
                ignorar_id,
            )

        resposta = consulta.execute()

        return bool(resposta.data)

    except Exception:
        return False


def adicionar_designacao(
    mes: str,
    data_texto: str,
    dia_semana: str,
    funcao: str,
    irmao: str,
):
    data_real = obter_data(data_texto)

    if not data_real:
        return False, "Digite uma data válida."

    if data_real.weekday() not in (0, 5):
        return (
            False,
            "A data deve ser uma segunda-feira ou sábado.",
        )

    if dia_semana == "seg" and data_real.weekday() != 0:
        return (
            False,
            "A data informada não corresponde a uma segunda-feira.",
        )

    if dia_semana == "sab" and data_real.weekday() != 5:
        return (
            False,
            "A data informada não corresponde a um sábado.",
        )

    if not mes.strip():
        return False, "Informe o mês."

    if not funcao.strip():
        return False, "Informe a função."

    if not irmao.strip():
        return False, "Informe o nome do irmão."

    if verificar_duplicidade(
        mes,
        data_texto,
        funcao,
    ):
        return (
            False,
            "Já existe uma designação para essa função nessa data.",
        )

    dados = {
        "mes": mes.strip(),
        "data_texto": data_texto.strip(),
        "dia_semana": dia_semana,
        "funcao": funcao.strip(),
        "irmao": irmao.strip(),
    }

    try:
        supabase.table("escalas").insert(
            dados
        ).execute()

        return True, "Designação adicionada."

    except Exception:
        return False, "Não foi possível adicionar a designação."


def editar_designacao(
    id_designacao,
    mes: str,
    data_texto: str,
    dia_semana: str,
    funcao: str,
    irmao: str,
):
    data_real = obter_data(data_texto)

    if not data_real:
        return False, "Digite uma data válida."

    if data_real.weekday() not in (0, 5):
        return (
            False,
            "A data deve ser uma segunda-feira ou sábado.",
        )

    if dia_semana == "seg" and data_real.weekday() != 0:
        return (
            False,
            "A data não corresponde a uma segunda-feira.",
        )

    if dia_semana == "sab" and data_real.weekday() != 5:
        return (
            False,
            "A data não corresponde a um sábado.",
        )

    if verificar_duplicidade(
        mes,
        data_texto,
        funcao,
        ignorar_id=id_designacao,
    ):
        return (
            False,
            "Já existe uma designação para essa função nessa data.",
        )

    dados = {
        "mes": mes.strip(),
        "data_texto": data_texto.strip(),
        "dia_semana": dia_semana,
        "funcao": funcao.strip(),
        "irmao": irmao.strip(),
    }

    try:
        (
            supabase
            .table("escalas")
            .update(dados)
            .eq("id", id_designacao)
            .execute()
        )

        return True, "Designação atualizada."

    except Exception:
        return False, "Não foi possível atualizar a designação."


def excluir_designacao(id_designacao):
    try:
        (
            supabase
            .table("escalas")
            .delete()
            .eq("id", id_designacao)
            .execute()
        )

        return True, "Designação excluída."

    except Exception:
        return False, "Não foi possível excluir a designação."


# ============================================================
# FUNÇÕES DE EXIBIÇÃO
# ============================================================

def mostrar_escala(mes: str, somente_irmao: Optional[str] = None):
    dados = buscar_escala(mes)

    if somente_irmao:
        nome_procurado = somente_irmao.strip().lower()

        dados = [
            item
            for item in dados
            if str(
                item.get("irmao", "")
            ).strip().lower() == nome_procurado
        ]

    if not dados:
        st.info("Nenhuma designação encontrada.")
        return

    datas = {}

    for item in dados:
        data_texto = item.get(
            "data_texto",
            "",
        )

        if data_texto not in datas:
            datas[data_texto] = []

        datas[data_texto].append(item)

    for data_texto, itens in datas.items():

        dia = str(
            itens[0].get("dia_semana", "")
        ).lower()

        if dia == "seg":
            classe = "segunda-feira"
            nome_dia = "Segunda-feira"
        elif dia == "sab":
            classe = "sabado"
            nome_dia = "Sábado"
        else:
            data_real = obter_data(data_texto)

            if data_real and data_real.weekday() == 0:
                classe = "segunda-feira"
                nome_dia = "Segunda-feira"
            elif data_real and data_real.weekday() == 5:
                classe = "sabado"
                nome_dia = "Sábado"
            else:
                classe = ""
                nome_dia = ""

        st.markdown(
            f"""
            <div class="card {classe}">
                <div class="data-escala">
                    📅 {data_texto}
                    {(" — " + nome_dia) if nome_dia else ""}
                </div>
            """,
            unsafe_allow_html=True,
        )

        for item in itens:
            funcao = item.get("funcao", "")
            irmao = item.get("irmao", "")

            st.markdown(
                f"""
                <div class="nome-irmao">
                    {irmao}
                </div>
                <div class="funcao">
                    {funcao}
                </div>
                <hr>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


# ============================================================
# LOGIN
# ============================================================

if not st.session_state.logado:

    st.markdown(
        '<div class="titulo-principal">📋 Designações Mecânicas</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitulo">Congregação Jardim América</div>',
        unsafe_allow_html=True,
    )

    tab_login, tab_cadastro = st.tabs(
        [
            "🔐 Entrar",
            "📝 Criar cadastro",
        ]
    )

    with tab_login:

        st.subheader("Entrar")

        email_login = st.text_input(
            "E-mail",
            key="email_login",
        )

        senha_login = st.text_input(
            "Senha",
            type="password",
            key="senha_login",
        )

        if st.button(
            "Entrar",
            type="primary",
            use_container_width=True,
        ):
            sucesso, usuario, mensagem = autenticar_usuario(
                email_login,
                senha_login,
            )

            if sucesso:
                st.session_state.usuario = usuario
                st.session_state.logado = True
                st.rerun()
            else:
                st.error(mensagem)

    with tab_cadastro:

        st.subheader("Criar cadastro")

        nome = st.text_input(
            "Nome completo",
            key="cad_nome",
        )

        email = st.text_input(
            "E-mail",
            key="cad_email",
        )

        telefone = st.text_input(
            "Telefone",
            key="cad_telefone",
        )

        senha = st.text_input(
            "Senha",
            type="password",
            key="cad_senha",
        )

        confirmar_senha = st.text_input(
            "Confirmar senha",
            type="password",
            key="cad_confirmar",
        )

        if st.button(
            "Cadastrar",
            type="primary",
            use_container_width=True,
        ):

            if senha != confirmar_senha:
                st.error("As senhas não são iguais.")

            else:
                sucesso, mensagem = cadastrar_usuario(
                    nome,
                    email,
                    senha,
                    telefone,
                )

                if sucesso:
                    st.success(mensagem)
                else:
                    st.error(mensagem)

    st.stop()


# ============================================================
# USUÁRIO LOGADO
# ============================================================

usuario = st.session_state.usuario

nome_usuario = usuario.get(
    "nome",
    "Usuário",
)

perfil_usuario = usuario.get(
    "perfil",
    "usuario",
)

st.markdown(
    '<div class="titulo-principal">📋 Designações Mecânicas</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitulo">Congregação Jardim América</div>',
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        f"### 👤 {nome_usuario}"
    )

    st.caption(
        f"Perfil: {perfil_usuario}"
    )

    if st.button(
        "🚪 Sair",
        use_container_width=True,
    ):
        fazer_logout()


# ============================================================
# ABAS
# ============================================================

if usuario_e_admin():

    (
        tab_escala,
        tab_minhas,
        tab_admin,
        tab_usuarios,
    ) = st.tabs(
        [
            "📋 Escala",
            "🔎 Minhas Designações",
            "⚙️ Gerenciar Escala",
            "👥 Usuários",
        ]
    )

else:

    (
        tab_escala,
        tab_minhas,
    ) = st.tabs(
        [
            "📋 Escala",
            "🔎 Minhas Designações",
        ]
    )


# ============================================================
# ABA ESCALA
# ============================================================

with tab_escala:

    st.header("📋 Escala")

    meses = buscar_meses()

    if not meses:
        st.info(
            "Ainda não existem meses cadastrados."
        )
    else:

        mes_selecionado = st.selectbox(
            "Selecione o mês",
            meses,
            key="mes_escala",
        )

        mostrar_escala(
            mes_selecionado
        )


# ============================================================
# ABA MINHAS DESIGNAÇÕES
# ============================================================

with tab_minhas:

    st.header("🔎 Minhas Designações")

    meses = buscar_meses()

    if not meses:
        st.info(
            "Ainda não existem designações."
        )

    else:

        mes_pessoal = st.selectbox(
            "Mês",
            meses,
            key="mes_pessoal",
        )

        if usuario_e_admin():

            nome_busca = st.text_input(
                "Nome do irmão",
                value=nome_usuario,
                key="nome_busca_admin",
            )

        else:

            nome_busca = nome_usuario

            st.info(
                f"Mostrando as designações de **{nome_usuario}**."
            )

        mostrar_escala(
            mes_pessoal,
            somente_irmao=nome_busca,
        )


# ============================================================
# ABA ADMINISTRADOR — GERENCIAR ESCALA
# ============================================================

if usuario_e_admin():

    with tab_admin:

        st.header("⚙️ Gerenciar Escala")

        meses = buscar_meses()

        if meses:
            mes_admin = st.selectbox(
                "Mês da escala",
                meses,
                key="mes_admin",
            )
        else:
            mes_admin = ""

        st.subheader("➕ Adicionar designação")

        col1, col2 = st.columns(2)

        with col1:

            novo_mes = st.text_input(
                "Mês",
                value=mes_admin,
                placeholder="Ex.: Outubro 2026",
            )

            nova_data = st.date_input(
                "Data",
                value=date.today(),
                format="DD/MM/YYYY",
            )

            novo_dia = st.selectbox(
                "Dia da reunião",
                options=[
                    "seg",
                    "sab",
                ],
                format_func=lambda x: DIAS_REUNIAO[x],
            )

        with col2:

            nova_funcao = st.selectbox(
                "Função",
                FUNCOES,
            )

            novo_irmao = st.text_input(
                "Irmão",
            )

        if st.button(
            "Adicionar designação",
            type="primary",
            use_container_width=True,
        ):

            if nova_data:

                data_formatada = nova_data.strftime(
                    "%d/%m/%Y"
                )

                sucesso, mensagem = adicionar_designacao(
                    novo_mes,
                    data_formatada,
                    novo_dia,
                    nova_funcao,
                    novo_irmao,
                )

                if sucesso:
                    st.success(mensagem)
                    st.rerun()
                else:
                    st.error(mensagem)

        st.divider()

        st.subheader("✏️ Designações cadastradas")

        if mes_admin:

            dados_admin = buscar_escala(
                mes_admin
            )

            if not dados_admin:
                st.info(
                    "Nenhuma designação cadastrada neste mês."
                )

            for item in dados_admin:

                with st.expander(
                    f"{item.get('data_texto', '')} — "
                    f"{item.get('funcao', '')} — "
                    f"{item.get('irmao', '')}"
                ):

                    col_a, col_b = st.columns(2)

                    with col_a:

                        editar_data = st.text_input(
                            "Data",
                            value=item.get(
                                "data_texto",
                                "",
                            ),
                            key=f"data_{item['id']}",
                        )

                        editar_dia = st.selectbox(
                            "Dia",
                            ["seg", "sab"],
                            index=(
                                0
                                if item.get(
                                    "dia_semana"
                                ) == "seg"
                                else 1
                            ),
                            format_func=lambda x: DIAS_REUNIAO[x],
                            key=f"dia_{item['id']}",
                        )

                    with col_b:

                        funcao_atual = item.get(
                            "funcao",
                            FUNCOES[0],
                        )

                        if funcao_atual in FUNCOES:
                            indice_funcao = FUNCOES.index(
                                funcao_atual
                            )
                        else:
                            indice_funcao = 0

                        editar_funcao = st.selectbox(
                            "Função",
                            FUNCOES,
                            index=indice_funcao,
                            key=f"funcao_{item['id']}",
                        )

                        editar_irmao = st.text_input(
                            "Irmão",
                            value=item.get(
                                "irmao",
                                "",
                            ),
                            key=f"irmao_{item['id']}",
                        )

                    col_salvar, col_excluir = st.columns(2)

                    with col_salvar:

                        if st.button(
                            "💾 Salvar alterações",
                            key=f"salvar_{item['id']}",
                            use_container_width=True,
                        ):

                            sucesso, mensagem = editar_designacao(
                                item["id"],
                                mes_admin,
                                editar_data,
                                editar_dia,
                                editar_funcao,
                                editar_irmao,
                            )

                            if sucesso:
                                st.success(mensagem)
                                st.rerun()
                            else:
                                st.error(mensagem)

                    with col_excluir:

                        if st.button(
                            "🗑️ Excluir",
                            key=f"excluir_{item['id']}",
                            use_container_width=True,
                        ):

                            sucesso, mensagem = excluir_designacao(
                                item["id"]
                            )

                            if sucesso:
                                st.success(mensagem)
                                st.rerun()
                            else:
                                st.error(mensagem)


# ============================================================
# ABA ADMINISTRADOR — USUÁRIOS
# ============================================================

if usuario_e_admin():

    with tab_usuarios:

        st.header("👥 Gerenciar usuários")

        try:

            resposta = (
                supabase
                .table("usuarios")
                .select(
                    "id,nome,email,telefone,status,perfil"
                )
                .order(
                    "nome"
                )
                .execute()
            )

            usuarios = resposta.data or []

        except Exception:

            usuarios = []

        if not usuarios:

            st.info(
                "Nenhum usuário cadastrado."
            )

        else:

            pendentes = [
                u
                for u in usuarios
                if str(
                    u.get("status", "")
                ).lower() == "pendente"
            ]

            aprovados = [
                u
                for u in usuarios
                if str(
                    u.get("status", "")
                ).lower() == "aprovado"
            ]

            st.subheader(
                f"⏳ Pendentes ({len(pendentes)})"
            )

            if not pendentes:

                st.info(
                    "Não há cadastros aguardando aprovação."
                )

            for u in pendentes:

                with st.container():

                    st.markdown(
                        f"""
                        <div class="card status-pendente">
                            <strong>{u.get('nome', '')}</strong><br>
                            {u.get('email', '')}<br>
                            Telefone: {u.get('telefone', '')}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    col_aprovar, col_rejeitar = st.columns(2)

                    with col_aprovar:

                        if st.button(
                            "✅ Aprovar",
                            key=f"aprovar_{u['id']}",
                            use_container_width=True,
                        ):

                            try:

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
                                        u["id"],
                                    )
                                    .execute()
                                )

                                st.success(
                                    "Usuário aprovado."
                                )

                                st.rerun()

                            except Exception:

                                st.error(
                                    "Não foi possível aprovar o usuário."
                                )

                    with col_rejeitar:

                        if st.button(
                            "❌ Rejeitar",
                            key=f"rejeitar_{u['id']}",
                            use_container_width=True,
                        ):

                            try:

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
                                        u["id"],
                                    )
                                    .execute()
                                )

                                st.success(
                                    "Usuário rejeitado."
                                )

                                st.rerun()

                            except Exception:

                                st.error(
                                    "Não foi possível rejeitar o usuário."
                                )

            st.divider()

            st.subheader(
                f"👤 Usuários aprovados ({len(aprovados)})"
            )

            for u in aprovados:

                st.markdown(
                    f"""
                    <div class="card status-aprovado">
                        <strong>{u.get('nome', '')}</strong><br>
                        {u.get('email', '')}<br>
                        Perfil: {u.get('perfil', 'usuario')}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ============================================================
# RODAPÉ
# ============================================================

st.divider()

st.caption(
    "Sistema de Designações Mecânicas — Congregação Jardim América"
)
