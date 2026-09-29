import streamlit as st
import os
from datetime import datetime
from supabase import create_client, Client


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Designações Mecânicas — Congregação Jardim América",
    page_icon="🏛️",
    layout="wide"
)


# ============================================================
# CONEXÃO COM SUPABASE
# ============================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]


@st.cache_resource
def get_supabase() -> Client:
    return create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )


try:
    supabase = get_supabase()

except Exception as e:
    st.error(
        f"Erro ao ligar ao banco de dados Supabase: {e}"
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


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        text-align: center;
        padding: 20px 10px 10px 10px;
    }

    .main-title h1 {
        margin-bottom: 5px;
    }

    .main-title p {
        color: #6B7280;
        font-size: 18px;
    }

    .scale-card {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 3px 12px rgba(0,0,0,0.10);
    }

    .scale-card h3 {
        margin-top: 0;
    }

    .function {
        margin-bottom: 12px;
    }

    .function-name {
        font-weight: 700;
        color: #111827;
    }

    .brother-name {
        color: #374151;
        font-size: 16px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def converter_data(data_texto):
    """
    Tenta localizar uma data no formato DD/MM/AAAA
    dentro do texto da data.
    """

    if not data_texto:
        return datetime.max

    try:
        texto = str(data_texto)

        partes = texto.split()

        for parte in partes:

            parte_limpa = (
                parte
                .replace("—", "")
                .replace("-", "")
                .strip()
            )

            if "/" in parte_limpa:

                try:
                    return datetime.strptime(
                        parte_limpa,
                        "%d/%m/%Y"
                    )

                except ValueError:
                    pass

    except Exception:
        pass

    return datetime.max


def formatar_data_titulo(data_texto):
    """
    Remove informações duplicadas da data quando possível.
    """

    if not data_texto:
        return "Data não informada"

    texto = str(data_texto).strip()

    # Se estiver no formato:
    # Sábado — 10/10/2026 — Sábado
    # transforma em:
    # Sábado — 10/10/2026

    partes = [
        p.strip()
        for p in texto.split("—")
        if p.strip()
    ]

    if len(partes) >= 2:

        primeira = partes[0]
        segunda = partes[1]

        if primeira.lower() == partes[-1].lower():
            return f"{primeira} — {segunda}"

    return texto


def obter_cor_reuniao(item):
    dia = str(
        item.get("dia_semana", "")
    ).lower()

    if dia == "sab":
        return "#7e22ce"

    return "#1e3a8a"


# ============================================================
# TELA DE LOGIN / CADASTRO
# ============================================================

if not st.session_state["logged_in"]:

    st.markdown(
        """
        <div class="main-title">

            <h1>
                🏛️ Portal de Designações Mecânicas
            </h1>

            <p>
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

                if not email_login:

                    st.warning(
                        "Digite o seu e-mail."
                    )

                elif not senha_login:

                    st.warning(
                        "Digite a sua palavra-passe."
                    )

                else:

                    try:

                        # ------------------------------------------------
                        # PRIMEIRO: PROCURAR O UTILIZADOR PELO E-MAIL
                        # ------------------------------------------------

                        resultado_usuario = (
                            supabase
                            .table("usuarios")
                            .select(
                                "id,nome,email,senha,telefone,status,perfil"
                            )
                            .ilike(
                                "email",
                                email_login
                            )
                            .execute()
                        )

                        if not resultado_usuario.data:

                            st.error(
                                "E-mail ou palavra-passe incorretos."
                            )

                        else:

                            user = resultado_usuario.data[0]

                            senha_banco = str(
                                user.get("senha", "")
                            )

                            senha_digitada = str(
                                senha_login
                            )

                            # --------------------------------------------
                            # CONFERIR SENHA
                            # --------------------------------------------

                            if senha_banco != senha_digitada:

                                st.error(
                                    "E-mail ou palavra-passe incorretos."
                                )

                            # --------------------------------------------
                            # CONFERIR STATUS
                            # --------------------------------------------

                            elif user.get("status") == "aprovado":

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

                                st.success(
                                    f"Bem-vindo, "
                                    f"{user.get('nome', '')}!"
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
            )

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
                            .ilike(
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
                                    "nome": nome_cad.strip(),
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

    perfil_atual = st.session_state.get(
        "user_role",
        "irmao"
    )

    st.sidebar.caption(
        f"Perfil: **{str(perfil_atual).upper()}**"
    )

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

        meses_disponiveis = sorted(
            list(
                set(
                    str(item["mes"]).strip()
                    for item in (res_meses.data or [])
                    if item.get("mes")
                )
            )
        )

    except Exception as err:

        st.sidebar.error(
            f"Erro ao buscar meses: {err}"
        )

        meses_disponiveis = []


    # ========================================================
    # SE NÃO HOUVER MESES
    # ========================================================

    if not meses_disponiveis:

        st.sidebar.info(
            "Nenhum mês possui escala cadastrada."
        )

        mes_selecionado = None

    else:

        mes_selecionado = st.sidebar.selectbox(
            "📅 Selecionar Mês:",
            meses_disponiveis,
            index=0
        )


    # ========================================================
    # BUSCAR ESCALAS
    # ========================================================

    if mes_selecionado:

        try:

            mes_consulta = str(
                mes_selecionado
            ).strip()

            res_escala = (
                supabase
                .table("escalas")
                .select("*")
                .eq("mes", mes_consulta)
                .execute()
            )

            dados_escala = (
                res_escala.data or []
            )

            st.sidebar.success(
                f"✅ {len(dados_escala)} registros encontrados"
            )

        except Exception as err:

            dados_escala = []

            st.sidebar.error(
                f"Erro ao buscar escalas: {err}"
            )

    else:

        dados_escala = []


    # ========================================================
    # ORGANIZAR DATAS
    # ========================================================

    datas_dict = {}

    for item in dados_escala:

        dt = item.get(
            "data_texto",
            "Data não informada"
        )

        if dt not in datas_dict:

            datas_dict[dt] = []

        datas_dict[dt].append({
            "id": item.get("id"),
            "funcao": item.get(
                "funcao",
                ""
            ),
            "irmao": item.get(
                "irmao",
                ""
            ),
            "dia_semana": item.get(
                "dia_semana",
                ""
            ),
            "mes": item.get(
                "mes",
                ""
            )
        })


    # ========================================================
    # ORDENAR AS DATAS
    # ========================================================

    lista_datas = sorted(
        datas_dict.keys(),
        key=converter_data
    )


    # ========================================================
    # ABAS
    # ========================================================

    if perfil_atual == "admin":

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
                    📅 {mes_selecionado or "Nenhum mês"}
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

            for i in range(
                0,
                len(lista_datas),
                2
            ):

                col1, col2 = st.columns(2)

                # =================================================
                # PRIMEIRA REUNIÃO
                # =================================================

                dt1 = lista_datas[i]

                itens1 = datas_dict[dt1]

                cor1 = obter_cor_reuniao(
                    itens1[0]
                )

                titulo1 = formatar_data_titulo(
                    dt1
                )

                with col1:

                    html1 = f"""
                    <div class="scale-card"
                         style="
                         border-left:6px solid {cor1};
                         ">

                        <h3 style="
                            color:{cor1};
                            margin-bottom:18px;
                        ">
                            📅 {titulo1}
                        </h3>
                    """

                    for item in itens1:

                        html1 += f"""
                        <div class="function">

                            <div class="function-name">
                                {item['funcao']}
                            </div>

                            <div class="brother-name">
                                {item['irmao']}
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


                # =================================================
                # SEGUNDA REUNIÃO
                # =================================================

                if i + 1 < len(lista_datas):

                    dt2 = lista_datas[i + 1]

                    itens2 = datas_dict[dt2]

                    cor2 = obter_cor_reuniao(
                        itens2[0]
                    )

                    titulo2 = formatar_data_titulo(
                        dt2
                    )

                    with col2:

                        html2 = f"""
                        <div class="scale-card"
                             style="
                             border-left:6px solid {cor2};
                             ">

                            <h3 style="
                                color:{cor2};
                                margin-bottom:18px;
                            ">
                                📅 {titulo2}
                            </h3>
                        """

                        for item in itens2:

                            html2 += f"""
                            <div class="function">

                                <div class="function-name">
                                    {item['funcao']}
                                </div>

                                <div class="brother-name">
                                    {item['irmao']}
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
            "🔍 Minhas Designações"
        )

        busca = st.text_input(
            "Digite o nome para consultar:",
            value=st.session_state["user_name"]
        )

        if busca:

            encontrado = False

            for dt in lista_datas:

                for item in datas_dict[dt]:

                    nome_irmao = str(
                        item.get(
                            "irmao",
                            ""
                        )
                    )

                    if busca.lower() in nome_irmao.lower():

                        st.success(
                            f"📅 **{formatar_data_titulo(dt)}** — "
                            f"**{item['funcao']}:** "
                            f"{item['irmao']}"
                        )

                        encontrado = True

            if not encontrado:

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


    # ========================================================
    # ABA 4 — ADMINISTRAR ESCALAS
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
                    value=(
                        mes_selecionado
                        or "2026-11"
                    )
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

                enviar = st.form_submit_button(
                    "➕ Adicionar à Escala",
                    type="primary",
                    use_container_width=True
                )

                if enviar:

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

                            # ------------------------------------
                            # VERIFICAR DUPLICAÇÃO
                            # ------------------------------------

                            duplicado = (
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

                            if duplicado.data:

                                st.warning(
                                    "Essa designação já "
                                    "está cadastrada."
                                )

                            else:

                                (
                                    supabase
                                    .table("escalas")
                                    .insert({
                                        "mes": mes_input.strip(),
                                        "data_texto": data_texto_input.strip(),
                                        "dia_semana": dia_sem_input,
                                        "funcao": funcao_input,
                                        "irmao": irmao_input.strip()
                                    })
                                    .execute()
                                )

                                st.success(
                                    "✅ Designação adicionada!"
                                )

                                st.rerun()

                        except Exception as err:

                            st.error(
                                f"Erro ao adicionar "
                                f"designação: {err}"
                            )


            # ====================================================
            # LISTA PARA EDITAR / EXCLUIR
            # ====================================================

            st.divider()

            st.subheader(
                "📝 Gerir Designações Existentes"
            )

            if not dados_escala:

                st.info(
                    "Não existem designações "
                    "neste mês."
                )

            else:

                for item in sorted(
                    dados_escala,
                    key=lambda x: converter_data(
                        x.get("data_texto", "")
                    )
                ):

                    item_id = item.get("id")

                    if item_id is None:
                        continue

                    titulo = (
                        f"{formatar_data_titulo(item.get('data_texto', ''))} "
                        f"— {item.get('funcao', '')} "
                        f"— {item.get('irmao', '')}"
                    )

                    with st.expander(
                        titulo
                    ):

                        c1, c2 = st.columns(2)

                        novo_nome = c1.text_input(
                            "Nome do Irmão:",
                            value=str(
                                item.get(
                                    "irmao",
                                    ""
                                )
                            ),
                            key=f"nome_{item_id}"
                        )

                        nova_funcao = c2.selectbox(
                            "Função:",
                            [
                                "🗣️ Oração Inicial",
                                "🗣️ Oração Final",
                                "📖 Leitor A Sentinela",
                                "🎤 Microfones",
                                "🚪 Ind. Entrada",
                                "🏛️ Ind. Auditório"
                            ],
                            index=(
                                [
                                    "🗣️ Oração Inicial",
                                    "🗣️ Oração Final",
                                    "📖 Leitor A Sentinela",
                                    "🎤 Microfones",
                                    "🚪 Ind. Entrada",
                                    "🏛️ Ind. Auditório"
                                ].index(
                                    item.get(
                                        "funcao",
                                        "🗣️ Oração Inicial"
                                    )
                                )
                                if item.get("funcao")
                                in [
                                    "🗣️ Oração Inicial",
                                    "🗣️ Oração Final",
                                    "📖 Leitor A Sentinela",
                                    "🎤 Microfones",
                                    "🚪 Ind. Entrada",
                                    "🏛️ Ind. Auditório"
                                ]
                                else 0
                            ),
                            key=f"funcao_{item_id}"
                        )

                        c3, c4 = st.columns(2)

                        nova_data = c3.text_input(
                            "Data:",
                            value=str(
                                item.get(
                                    "data_texto",
                                    ""
                                )
                            ),
                            key=f"data_{item_id}"
                        )

                        novo_dia = c4.selectbox(
                            "Tipo de Reunião:",
                            ["seg", "sab"],
                            index=(
                                0
                                if item.get(
                                    "dia_semana"
                                ) != "sab"
                                else 1
                            ),
                            format_func=lambda x:
                                "Segunda-feira"
                                if x == "seg"
                                else "Sábado",
                            key=f"dia_{item_id}"
                        )

                        b1, b2 = st.columns(2)

                        if b1.button(
                            "💾 Guardar Alterações",
                            key=f"save_{item_id}",
                            use_container_width=True
                        ):

                            try:

                                (
                                    supabase
                                    .table("escalas")
                                    .update({
                                        "irmao": novo_nome.strip(),
                                        "funcao": nova_funcao,
                                        "data_texto": nova_data.strip(),
                                        "dia_semana": novo_dia
                                    })
                                    .eq(
                                        "id",
                                        item_id
                                    )
                                    .execute()
                                )

                                st.success(
                                    "✅ Alterações guardadas."
                                )

                                st.rerun()

                            except Exception as err:

                                st.error(
                                    f"Erro ao atualizar: {err}"
                                )

                        if b2.button(
                            "🗑️ Excluir",
                            key=f"delete_{item_id}",
                            use_container_width=True
                        ):

                            try:

                                (
                                    supabase
                                    .table("escalas")
                                    .delete()
                                    .eq(
                                        "id",
                                        item_id
                                    )
                                    .execute()
                                )

                                st.success(
                                    "✅ Designação excluída."
                                )

                                st.rerun()

                            except Exception as err:

                                st.error(
                                    f"Erro ao excluir: {err}"
                                )


    # ========================================================
    # PAINEL DO ADMIN
    # ========================================================

    if perfil_atual == "admin":

        st.sidebar.markdown("---")

        st.sidebar.subheader(
            "⚙️ Aprovar Utilizadores"
        )

        try:

            pendentes = (
                supabase
                .table("usuarios")
                .select("*")
                .eq(
                    "status",
                    "pendente"
                )
                .execute()
            )

            if pendentes.data:

                for u in pendentes.data:

                    st.sidebar.write(
                        f"👤 **{u.get('nome', '')}** "
                        f"({u.get('telefone', 'Sem tel')})"
                    )

                    c_ap, c_rec = (
                        st.sidebar.columns(2)
                    )

                    # ----------------------------------------
                    # APROVAR
                    # ----------------------------------------

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
                            .eq(
                                "id",
                                u["id"]
                            )
                            .execute()
                        )

                        st.rerun()

                    # ----------------------------------------
                    # RECUSAR
                    # ----------------------------------------

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
                            .eq(
                                "id",
                                u["id"]
                            )
                            .execute()
                        )

                        st.rerun()

            else:

                st.sidebar.caption(
                    "Nenhum utilizador pendente."
                )

        except Exception as err:

            st.sidebar.error(
                f"Erro ao carregar utilizadores: {err}"
            )
