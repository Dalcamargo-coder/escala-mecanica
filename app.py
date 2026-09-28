import streamlit as st
import base64
import os

# 1. Configuração da Página em Ecrã Inteiro (WIDE)
st.set_page_config(
    page_title="Designações Mecânicas - Jardim América",
    page_icon="📅",
    layout="wide"  # <--- Ajustado para usar 100% da largura da tela!
)

# 2. Palavras-passe de Acesso
PASSWORD_USER = "irmaos2026"
PASSWORD_ADMIN = "admin2026"

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None

# --- TELA DE LOGIN ---
if not st.session_state["logged_in"]:
    st.title("🔒 Acesso à Escala de Designações Mecânicas")
    st.subheader("Congregação Jardim América")
    
    tipo_acesso = st.radio("Selecione o tipo de acesso:", ["Irmão (Consulta)", "Administrador"])
    senha = st.text_input("Palavra-passe de Acesso:", type="password")
    
    if st.button("Entrar", use_container_width=True):
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

    st.title("📅 Escala de Designações Mecânicas")
    st.caption("Congregação Jardim América")
    st.divider()

    pdf_path = "Designações_Mecânicas_-_Outubro_2026.pdf"

    # --- VISUALIZAÇÃO E DOWNLOAD DO PDF OFICIAL EM TAMANHO REAL ---
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        st.download_button(
            label="📄 Baixar / Imprimir PDF Oficial (A4)",
            data=pdf_bytes,
            file_name=pdf_path,
            mime="application/pdf",
            use_container_width=True
        )

        st.markdown("### 📜 Visualização da Folha Completa (A4)")
        # Codifica o PDF para exibir em tamanho A4 completo dentro do site (1000px de altura)
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="1000px" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.info("ℹ️ O ficheiro PDF estará disponível assim que for carregado no GitHub.")

    st.divider()

    # Painel do Admin
    if st.session_state["user_role"] == "admin":
        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Painel do Administrador")
        st.sidebar.write("Painel reservado para gestão e envio de novas apostilas.")
