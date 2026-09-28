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
    st.error("Erro ao ligar ao banco de dados Supabase. Verifique a chave de API.")

# 3. Estado da Sessão
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None

# --- TELA DE AUTENTICAÇÃO (LOGIN / REGISTO) ---
if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>🏛️ Portal de Designações Mecânicas</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6B7280;'>Congregação Jardim América</p>", unsafe_allow_html=True)
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_cadastro = st.tabs(["🔑 Entrar na Conta", "📝 Criar Nova Conta"])

        # ABA LOGIN
        with tab_login:
            st.subheader("Acesso dos Irmãos")
            email_login = st.text_input("E-mail registado:", key="login_email").strip().lower()
            senha_login = st.text_input("Palavra-passe:", type="password", key="login_senha")

            if st.button("Entrar no Portal", type="primary", use_container_width=True):
                if email_login and senha_login:
                    try:
                        res = supabase.table("usuarios").select("*").eq("email", email_login).eq("senha", senha_login).execute()
                        if res.data:
                            user = res.data[0]
                            if user["status"] == "aprovado":
                                st.session_state["logged_in"] = True
                                st.session_state["user_name"] = user["nome"]
                                st.session_state["user_role"] = user["perfil"]
                                st.success(f"Bem-vindo, {user['nome']}!")
                                st.rerun()
                            elif user["status"] == "pendente":
                                st.warning("⏳ O seu registo ainda está pendente de autorização pelo Administrador.")
                            else:
                                st.error("❌ O seu pedido de acesso não foi aprovado.")
                        else:
                            st.error("E-mail ou palavra-passe incorretos.")
                    except Exception as err:
                        st.error(f"Erro ao verificar conta: {err}")
                else:
                    st.warning("Preencha o e-mail e a palavra-passe.")

        # ABA REGISTO / CADASTRO
        with tab_cadastro:
            st.subheader("Registo de Novo Irmão")
            st.caption("O seu registo precisará de ser aprovado pelo Administrador antes de aceder.")
            nome_cad = st.text_input("Nome Completo:")
            email_cad = st.text_input("E-mail:").strip().lower()
            senha_cad = st.text_input("Crie uma Palavra-passe:", type="password")

            if st.button("Enviar Pedido de Registo", use_container_width=True):
                if nome_cad and email_cad and senha_cad:
                    try:
                        # Verificar se e-mail já existe
                        check = supabase.table("usuarios").select("id").eq("email", email_cad).execute()
                        if check.data:
                            st.error("Este e-mail já está registado no sistema.")
                        else:
                            supabase.table("usuarios").insert({
                                "nome": nome_cad,
                                "email": email_cad,
                                "senha": senha_cad,
                                "status": "pendente",
                                "perfil": "irmao"
                            }).execute()
                            st.success("✅ Registo enviado com sucesso! Aguarde a aprovação do Administrador.")
                    except Exception as err:
                        st.error(f"Erro ao realizar registo: {err}")
                else:
                    st.warning("Por favor, preencha todos os campos.")

# --- ÁREA INTERNA DO SITE LOGADO ---
else:
    # Barra Lateral
    st.sidebar.title("🏛️ Jardim América")
    st.sidebar.write(f"👤 **{st.session_state['user_name']}**")
    st.sidebar.caption(f"Perfil: **{st.session_state['user_role'].upper()}**")
    
    if st.sidebar.button("🚪 Terminar Sessão", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["user_name"] = ""
        st.session_state["user_role"] = None
        st.rerun()

    # Estrutura de Páginas do Portal
    semanas = [
        {
            "data_seg": "Segunda-feira — 05/10/2026",
            "seg": {"🗣️ Oração Inicial": "Marcel Silvério", "🗣️ Oração Final": "Adalberto Camargo", "🎤 Microfones": "Adalberto Camargo / Laércio Paulino", "🚪 Ind. Entrada": "Laércio Paulino", "🏛️ Ind. Auditório": "Marcel Silvério"},
            "data_sab": "Sábado — 10/10/2026",
            "sab": {"🗣️ Oração Final": "Gabriel Pereira", "📖 Leitor A Sentinela": "Jamenson Lisboa", "🎤 Microfones": "Gabriel Pereira / Jairo Damasceno", "🚪 Ind. Entrada": "Jairo Damasceno", "🏛️ Ind. Auditório": "Ricardo Maciel"}
        },
        {
            "data_seg": "Segunda-feira — 12/10/2026",
            "seg": {"🗣️ Oração Inicial": "Ueldson Lisboa", "🗣️ Oração Final": "Uilson Lisboa", "🎤 Microfones": "Ueldson Lisboa / Uilson Lisboa", "🚪 Ind. Entrada": "Marcio Silva", "🏛️ Ind. Auditório": "Enio Gomes"},
            "data_sab": "Sábado — 17/10/2026",
            "sab": {"🗣️ Oração Final": "Marcelo Carrera", "📖 Leitor A Sentinela": "Renê Mordente", "🎤 Microfones": "Marcelo Carrera / Samuel Schnetes", "🚪 Ind. Entrada": "Samuel Schnetes", "🏛️ Ind. Auditório": "Gesaías Vencato"}
        },
        {
            "data_seg": "Segunda-feira — 19/10/2026",
            "seg": {"🗣️ Oração Inicial": "Jairo Damasceno", "🗣️ Oração Final": "Ricardo Maciel", "🎤 Microfones": "Jairo Damasceno / Ricardo Maciel", "🚪 Ind. Entrada": "Adalberto Camargo", "🏛️ Ind. Auditório": "Laércio Paulino"},
            "data_sab": "Sábado — 24/10/2026",
            "sab": {"🗣️ Oração Final": "Gesaías Vencato", "📖 Leitor A Sentinela": "Lucas Carbinatto", "🎤 Microfones": "Gesaías Vencato / Gabriel Carbinatto", "🚪 Ind. Entrada": "Gabriel Carbinatto", "🏛️ Ind. Auditório": "Samuel Schnetes"}
        },
        {
            "data_seg": "Segunda-feira — 26/10/2026",
            "seg": {"🗣️ Oração Inicial": "Enio Gomes", "🗣️ Oração Final": "Marcio Silva", "🎤 Microfones": "Enio Gomes / Marcio Silva", "🚪 Ind. Entrada": "Marcel Silvério", "🏛️ Ind. Auditório": "Adalberto Camargo"},
            "data_sab": "Sábado — 31/10/2026",
            "sab": {"🗣️ Oração Final": "Gabriel Carbinatto", "📖 Leitor A Sentinela": "Lucas Valler", "🎤 Microfones": "Gabriel Carbinatto / Samuel Schnetes", "🚪 Ind. Entrada": "Samuel Schnetes", "🏛️ Ind. Auditório": "Gesaías Vencato"}
        }
    ]

    tab1, tab2, tab3 = st.tabs(["📅 Escala do Mês", "🔍 Procurar por Irmão", "📄 Imprimir PDF"])

    # TAB 1: ESCALA COMPLETA
    with tab1:
        st.subheader("📋 Designações Mecânicas — Outubro 2026")
        for sem in semanas:
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"🔹 **{sem['data_seg']}**")
                for k, v in sem["seg"].items():
                    st.write(f"**{k}:** {v}")
            with c2:
                st.success(f"🟣 **{sem['data_sab']}**")
                for k, v in sem["sab"].items():
                    st.write(f"**{k}:** {v}")
            st.divider()

    # TAB 2: FILTRO POR NOME
    with tab2:
        st.subheader("🔍 Minhas Designações")
        busca = st.text_input("Digite o seu nome para consultar:", value=st.session_state["user_name"].split()[0] if st.session_state["user_name"] else "")
        if busca:
            encontrado = False
            for sem in semanas:
                for func, irmao in sem["seg"].items():
                    if busca.lower() in irmao.lower():
                        st.info(f"📅 **{sem['data_seg']}** — **{func}:** {irmao}")
                        encontrado = True
                for func, irmao in sem["sab"].items():
                    if busca.lower() in irmao.lower():
                        st.success(f"📅 **{sem['data_sab']}** — **{func}:** {irmao}")
                        encontrado = True
            if not encontrado:
                st.warning("Nenhuma designação localizada para este nome.")

    # TAB 3: DOWNLOAD PDF
    with tab3:
        st.subheader("📄 Documento Oficial para Impressão (Folha A4)")
        pdf_path = "Designações_Mecânicas_-_Outubro_2026.pdf"
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

    # PAINEL DE GESTÃO DO ADMINISTRADOR
    if st.session_state["user_role"] == "admin":
        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Gestão de Utilizadores")
        
        try:
            pendentes = supabase.table("usuarios").select("*").eq("status", "pendente").execute()
            if pendentes.data:
                st.sidebar.warning(f"📩 {len(pendentes.data)} pedido(s) de acesso pendente(s)!")
                for u in pendentes.data:
                    st.sidebar.write(f"👤 **{u['nome']}**\n📧 {u['email']}")
                    col_ap, col_rec = st.sidebar.columns(2)
                    if col_ap.button("✅ Aprovar", key=f"ap_{u['id']}", use_container_width=True):
                        supabase.table("usuarios").update({"status": "aprovado"}).eq("id", u["id"]).execute()
                        st.sidebar.success("Aprovado!")
                        st.rerun()
                    if col_rec.button("❌ Recusar", key=f"rec_{u['id']}", use_container_width=True):
                        supabase.table("usuarios").update({"status": "recusado"}).eq("id", u["id"]).execute()
                        st.sidebar.info("Recusado.")
                        st.rerun()
                    st.sidebar.markdown("---")
            else:
                st.sidebar.success("Nenhum pedido pendente.")
        except Exception as e:
            st.sidebar.error(f"Erro ao carregar registos: {e}")
