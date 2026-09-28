mport streamlit as st
import os

# 1. Configuração da Página
st.set_page_config(
    page_title="Designações Mecânicas — Congregação Jardim América",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Estilo CSS Personalizado Profissional
st.markdown("""
    <style>
    /* Estilização Geral */
    .stApp {
        background-color: #F8F9FA;
    }
    /* Estilo dos Cartões de Reunião */
    .card-segunda {
        background-color: #FFFFFF;
        border-left: 6px solid #4B5563;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 12px;
    }
    .card-sabado {
        background-color: #FFFFFF;
        border-left: 6px solid #1E40AF;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 12px;
    }
    .badge-funcao {
        font-weight: 700;
        color: #374151;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Credenciais de Acesso
PASSWORD_USER = "irmaos2026"
PASSWORD_ADMIN = "admin2026"

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None

# --- TELA DE LOGIN PROFISSIONAL ---
if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center; color: #1F2937;'>🏛️ portal de Designações</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6B7280;'>Congregação Jardim América — Testemunhas de Jeová</p>", unsafe_allow_html=True)
    
    col_centered = st.columns([1, 2, 1])[1]
    with col_centered:
        with st.container(border=True):
            st.subheader("🔑 Autenticação de Acesso")
            tipo_acesso = st.radio("Selecione o seu perfil:", ["Irmão (Consulta)", "Administrador"], horizontal=True)
            senha = st.text_input("Palavra-passe:", type="password")
            
            if st.button("Aceder ao Portal", use_container_width=True, type="primary"):
                if tipo_acesso == "Irmão (Consulta)" and senha == PASSWORD_USER:
                    st.session_state["logged_in"] = True
                    st.session_state["user_role"] = "user"
                    st.rerun()
                elif tipo_acesso == "Administrador" and senha == PASSWORD_ADMIN:
                    st.session_state["logged_in"] = True
                    st.session_state["user_role"] = "admin"
                    st.rerun()
                else:
                    st.error("Palavra-passe incorreta.")

# --- ÁREA PRINCIPAL DO PORTAL ---
else:
    # Barra Lateral
    st.sidebar.title("🏛️ Jardim América")
    st.sidebar.caption(f"Sessão Ativa: **{st.session_state['user_role'].upper()}**")
    if st.sidebar.button("🚪 Encerrar Sessão", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["user_role"] = None
        st.rerun()

    # Dados da Escala de Outubro 2026
    semanas = [
        {
            "semana": "Semana 1",
            "data_seg": "Segunda-feira — 05/10/2026",
            "seg": {"🗣️ Oração Inicial": "Marcel Silvério", "🗣️ Oração Final": "Adalberto Camargo", "🎤 Microfones": "Adalberto Camargo / Laércio Paulino", "🚪 Ind. Entrada": "Laércio Paulino", "🏛️ Ind. Auditório": "Marcel Silvério"},
            "data_sab": "Sábado — 10/10/2026",
            "sab": {"🗣️ Oração Final": "Gabriel Pereira", "📖 Leitor A Sentinela": "Jamenson Lisboa", "🎤 Microfones": "Gabriel Pereira / Jairo Damasceno", "🚪 Ind. Entrada": "Jairo Damasceno", "🏛️ Ind. Auditório": "Ricardo Maciel"}
        },
        {
            "semana": "Semana 2",
            "data_seg": "Segunda-feira — 12/10/2026",
            "seg": {"🗣️ Oração Inicial": "Ueldson Lisboa", "🗣️ Oração Final": "Uilson Lisboa", "🎤 Microfones": "Ueldson Lisboa / Uilson Lisboa", "🚪 Ind. Entrada": "Marcio Silva", "🏛️ Ind. Auditório": "Enio Gomes"},
            "data_sab": "Sábado — 17/10/2026",
            "sab": {"🗣️ Oração Final": "Marcelo Carrera", "📖 Leitor A Sentinela": "Renê Mordente", "🎤 Microfones": "Marcelo Carrera / Samuel Schnetes", "🚪 Ind. Entrada": "Samuel Schnetes", "🏛️ Ind. Auditório": "Gesaías Vencato"}
        },
        {
            "semana": "Semana 3",
            "data_seg": "Segunda-feira — 19/10/2026",
            "seg": {"🗣️ Oração Inicial": "Jairo Damasceno", "🗣️ Oração Final": "Ricardo Maciel", "🎤 Microfones": "Jairo Damasceno / Ricardo Maciel", "🚪 Ind. Entrada": "Adalberto Camargo", "🏛️ Ind. Auditório": "Laércio Paulino"},
            "data_sab": "Sábado — 24/10/2026",
            "sab": {"🗣️ Oração Final": "Gesaías Vencato", "📖 Leitor A Sentinela": "Lucas Carbinatto", "🎤 Microfones": "Gesaías Vencato / Gabriel Carbinatto", "🚪 Ind. Entrada": "Gabriel Carbinatto", "🏛️ Ind. Auditório": "Samuel Schnetes"}
        },
        {
            "semana": "Semana 4",
            "data_seg": "Segunda-feira — 26/10/2026",
            "seg": {"🗣️ Oração Inicial": "Enio Gomes", "🗣️ Oração Final": "Marcio Silva", "🎤 Microfones": "Enio Gomes / Marcio Silva", "🚪 Ind. Entrada": "Marcel Silvério", "🏛️ Ind. Auditório": "Adalberto Camargo"},
            "data_sab": "Sábado — 31/10/2026",
            "sab": {"🗣️ Oração Final": "Gabriel Carbinatto", "📖 Leitor A Sentinela": "Lucas Valler", "🎤 Microfones": "Gabriel Carbinatto / Samuel Schnetes", "🚪 Ind. Entrada": "Samuel Schnetes", "🏛️ Ind. Auditório": "Gesaías Vencato"}
        }
    ]

    # Separadores Principais
    tab1, tab2, tab3 = st.tabs(["📅 Escala do Mês", "🔍 Procurar por Irmão", "📄 Imprimir PDF"])

    # TAB 1: VISÃO GERAL
    with tab1:
        st.subheader("📋 Escala de Designações Mecânicas — Outubro 2026")
        for sem in semanas:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"### 🔹 {sem['data_seg']}")
                for k, v in sem["seg"].items():
                    st.write(f"**{k}:** {v}")
            with c2:
                st.markdown(f"### 🟣 {sem['data_sab']}")
                for k, v in sem["sab"].items():
                    st.write(f"**{k}:** {v}")
            st.divider()

    # TAB 2: PROCURAR POR IRMÃO
    with tab2:
        st.subheader("🔍 Consultar Minhas Designações")
        nome_busca = st.text_input("Digite o seu nome para filtrar:", placeholder="Ex: Jamenson, Lucas, Gabriel...")
        
        if nome_busca:
            encontrado = False
            st.markdown(f"#### Resultados para: **{nome_busca}**")
            for sem in semanas:
                # Busca na segunda
                for func, irmao in sem["seg"].items():
                    if nome_busca.lower() in irmao.lower():
                        st.info(f"📅 **{sem['data_seg']}** — **{func}:** {irmao}")
                        encontrado = True
                # Busca no sábado
                for func, irmao in sem["sab"].items():
                    if nome_busca.lower() in irmao.lower():
                        st.success(f"📅 **{sem['data_sab']}** — **{func}:** {irmao}")
                        encontrado = True
            if not encontrado:
                st.warning("Nenhuma designação encontrada para o nome digitado neste mês.")

    # TAB 3: DOWNLOAD DO PDF
    with tab3:
        st.subheader("📄 Documento Oficial Formatado (Folha A4)")
        pdf_path = "Designações_Mecânicas_-_Outubro_2026.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="🖨️ Descarregar / Imprimir PDF Oficial de Outubro 2026",
                    data=f.read(),
                    file_name=pdf_path,
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
        else:
            st.info("ℹ️ Ficheiro PDF não localizado no servidor.")

    # PAINEL EXCLUSIVO DO ADMIN
    if st.session_state["user_role"] == "admin":
        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Painel de Controlo")
        
        with st.sidebar.expander("📤 Enviar Novo PDF do Mês"):
            uploaded_file = st.file_uploader("Carregar PDF:", type="pdf")
            if uploaded_file is not None:
                with open(os.path.join(".", uploaded_file.name), "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("Ficheiro carregado com sucesso!")
