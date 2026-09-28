import streamlit as st
import os

# 1. Configuração da Página
st.set_page_config(
    page_title="Designações Mecânicas - Jardim América",
    page_icon="📅",
    layout="centered"
)

# 2. Palavras-passe de Acesso
PASSWORD_USER = "irmaos2026"  # Senha para os irmãos apenas visualizarem
PASSWORD_ADMIN = "admin2026"  # Senha do Administrador (Você)

# 3. Controlo de Login
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None

# --- TELA DE LOGIN ---
if not st.session_state["logged_in"]:
    st.title("🔒 Acesso à Escala de Designações")
    st.subheader("Congregação Jardim América")
    
    tipo_acesso = st.radio("Selecione o tipo de acesso:", ["Irmão (Consulta)", "Administrador"])
    senha = st.text_input("Palavra-passe de Acesso:", type="password")
    
    if st.button("Entrar"):
        if tipo_acesso == "Irmão (Consulta)" and senha == PASSWORD_USER:
            st.session_state["logged_in"] = True
            st.session_state["user_role"] = "user"
            st.rerun()
        elif tipo_acesso == "Administrador" and senha == PASSWORD_ADMIN:
            st.session_state["logged_in"] = True
            st.session_state["user_role"] = "admin"
            st.rerun()
        else:
            st.error("Palavra-passe incorreta. Tente novamente.")

# --- ÁREA DO SITE ---
else:
    st.sidebar.write(f"👤 **Perfil:** {st.session_state['user_role'].upper()}")
    if st.sidebar.button("Sair / Logout"):
        st.session_state["logged_in"] = False
        st.session_state["user_role"] = None
        st.rerun()

    st.title("📅 Designações Mecânicas")
    st.caption("Congregação Jardim América — Outubro / Novembro 2026")
    st.divider()

    # Botão de Download do PDF Oficial
    pdf_path = "Designações_Mecânicas_-_Outubro_2026.pdf"
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="📄 Baixar / Imprimir PDF Oficial (A4)",
                data=f,
                file_name=pdf_path,
                mime="application/pdf",
                use_container_width=True
            )
    else:
        st.info("ℹ️ O PDF oficial estará disponível para download assim que for carregado.")

    st.divider()
    st.subheader("📋 Escala de Outubro 2026 (Visão Rápida)")

    # Dados da Escala em Cartões
    semanas = [
        {
            "data_seg": "Segunda-feira — 05/10/2026",
            "seg": {"Ora. Inicial": "Marcel Silvério", "Ora. Final": "Adalberto Camargo", "Microfones": "Adalberto Camargo / Laércio Paulino", "Ind. Entrada": "Laércio Paulino", "Ind. Auditório": "Marcel Silvério"},
            "data_sab": "Sábado — 10/10/2026",
            "sab": {"Ora. Final": "Gabriel Pereira", "Leitor Sentinela": "Jamenson Lisboa", "Microfones": "Gabriel Pereira / Jairo Damasceno", "Ind. Entrada": "Jairo Damasceno", "Ind. Auditório": "Ricardo Maciel"}
        },
        {
            "data_seg": "Segunda-feira — 12/10/2026",
            "seg": {"Ora. Inicial": "Ueldson Lisboa", "Ora. Final": "Uilson Lisboa", "Microfones": "Ueldson Lisboa / Uilson Lisboa", "Ind. Entrada": "Marcio Silva", "Ind. Auditório": "Enio Gomes"},
            "data_sab": "Sábado — 17/10/2026",
            "sab": {"Ora. Final": "Marcelo Carrera", "Leitor Sentinela": "Renê Mordente", "Microfones": "Marcelo Carrera / Samuel Schnetes", "Ind. Entrada": "Samuel Schnetes", "Ind. Auditório": "Gesaías Vencato"}
        }
    ]

    for semana in semanas:
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"🔹 **{semana['data_seg']}**")
            for k, v in semana["seg"].items():
                st.write(f"**{k}:** {v}")
        with col2:
            st.success(f"🟣 **{semana['data_sab']}**")
            for k, v in semana["sab"].items():
                st.write(f"**{k}:** {v}")
        st.divider()

    # Painel exclusivo do Admin
    if st.session_state["user_role"] == "admin":
        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Painel do Administrador")
        st.sidebar.write("Espaço reservado para gestão e envio de novas apostilas.")
