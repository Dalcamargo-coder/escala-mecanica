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
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp3c3RnaW56dWltcmJ2dmF2cmx2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA2MjIwNDgsImV4cCI6MjEwNjE5ODA0OH0.XNLaxpWCElIntlXWS6_moHHCnzkTXUXBhcFoRx6K93M"  # <--- COLE A SUA CHAVE ANON AQUI

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

    col1, col2, col3 = st.columns(3)
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
            tel_cad = st.text_input("WhatsApp (com DDD, ex: 5519983035946):").strip()
            senha_cad = st.text_input("Crie uma Palavra-passe:", type="password")

            if st.button("Enviar Pedido de Registo", use_container_width=True):
                if nome_cad and email_cad and senha_cad and tel_cad:
                    try:
                        check = supabase.table("usuarios").select("id").eq("email", email_cad).execute()
                        if check.data:
                            st.error("Este e-mail já está registado no sistema.")
                        else:
                            supabase.table("usuarios").insert({
                                "nome": nome_cad,
                                "email": email_cad,
                                "telefone": tel_cad,
                                "senha": senha_cad,
                                "status": "pendente",
                                "perfil": "irmao"
                            }).execute()
                            st.success("✅ Registo enviado com sucesso! Aguarde a aprovação do Administrador.")
                    except Exception as err:
                        st.error(f"Erro ao realizar registo: {err}")
                else:
                    st.warning("Por favor, preencha todos os campos (incluindo o WhatsApp).")

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

    # Buscar meses disponíveis no banco de dados Supabase
    try:
        res_meses = supabase.table("escalas").select("mes").execute()
        meses_disponiveis = sorted(list(set([m["mes"] for m in res_meses.data]))) if res_meses.data else ["2026-10"]
    except Exception:
        meses_disponiveis = ["2026-10"]

    if "2026-10" not in meses_disponiveis:
        meses_disponiveis.insert(0, "2026-10")

    # Seleção do Mês
    mes_selecionado = st.sidebar.selectbox("📅 Selecionar Mês da Escala:", meses_disponiveis, index=0)

    # Buscar dados da escala do mês selecionado
    try:
        res_escala = supabase.table("escalas").select("*").eq("mes", mes_selecionado).execute()
        dados_escala = res_escala.data if res_escala.data else []
    except Exception as e:
        dados_escala = []
        st.error(f"Erro ao carregar escala do banco de dados: {e}")

    # Organizar dados por datas
    datas_dict = {}
    for item in dados_escala:
        dt = item["data_texto"]
        if dt not in datas_dict:
            datas_dict[dt] = []
        datas_dict[dt].append({"funcao": item["funcao"], "irmao": item["irmao"], "dia_semana": item.get("dia_semana", "seg")})

    # Abas principais
    if st.session_state["user_role"] == "admin":
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Escala do Mês", "🔍 Procurar por Irmão", "📄 Imprimir PDF", "⚙️ Gerir Escalas"])
    else:
        tab1, tab2, tab3 = st.tabs(["📅 Escala do Mês", "🔍 Procurar por Irmão", "📄 Imprimir PDF"])
        tab4 = None

    # TAB 1: ESCALA COMPLETA
    with tab1:
        st.subheader(f"📋 Designações Mecânicas — Mês {mes_selecionado}")
        if not datas_dict:
            st.info("Nenhuma escala registada no banco de dados para este mês.")
        else:
            lista_datas = list(datas_dict.keys())
            for i in range(0, len(lista_datas), 2):
                c1, c2 = st.columns(2)
                dt1 = lista_datas[i]
                with c1:
                    st.info(f"🔹 **{dt1}**")
                    for item in datas_dict[dt1]:
                        st.write(f"**{item['funcao']}:** {item['irmao']}")
                
                if i + 1 < len(lista_datas):
                    dt2 = lista_datas[i+1]
                    with c2:
                        st.success(f"🟣 **{dt2}**")
                        for item in datas_dict[dt2]:
                            st.write(f"**{item['funcao']}:** {item['irmao']}")
                st.divider()

    # TAB 2: FILTRO POR NOME
    with tab2:
        st.subheader("🔍 Minhas Designações")
        busca = st.text_input("Digite o seu nome para consultar:", value=st.session_state["user_name"])
        if busca:
            encontrado = False
            for dt, itens in datas_dict.items():
                for item in itens:
                    if busca.lower() in item["irmao"].lower():
                        st.success(f"📅 **{dt}** — **{item['funcao']}:** {item['irmao']}")
                        encontrado = True
            if not encontrado:
                st.warning("Nenhuma designação localizada para este nome no mês selecionado.")

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
        else:
            st.warning("Ficheiro PDF não encontrado no servidor.")

    # TAB 4: GESTÃO DE ESCALAS (Apenas Administrador)
    if tab4 is not None:
        with tab4:
            st.subheader("⚙️ Cadastrar Nova Designação na Escala")
            with st.form("form_nova_designacao"):
                c_mes, c_dia = st.columns(2)
                mes_input = c_mes.text_input("Mês (Ano-Mês):", value="2026-11", help="Exemplo: 2026-11 para Novembro")
                data_texto_input = c_dia.text_input("Data Formatada:", value="Segunda-feira — 02/11/2026")
                
                c_func, c_irm = st.columns(2)
                funcao_input = c_func.selectbox("Função:", [
                    "🗣️ Oração Inicial", 
                    "🗣️ Oração Final", 
                    "📖 Leitor A Sentinela", 
                    "🎤 Microfones", 
                    "🚪 Ind. Entrada", 
                    "🏛️ Ind. Auditório"
                ])
                irmao_input = c_irm.text_input("Nome do Irmão:")
                dia_sem_input = st.selectbox("Tipo de Reunião:", ["seg", "sab"], format_func=lambda x: "Meio de Semana (Segunda)" if x == "seg" else "Fim de Semana (Sábado)")
                
                if st.form_submit_button("➕ Adicionar à Escala", type="primary", use_container_width=True):
                    if mes_input and data_texto_input and irmao_input:
                        try:
                            supabase.table("escalas").insert({
                                "mes": mes_input,
                                "data_texto": data_texto_input,
                                "dia_semana": dia_sem_input,
                                "funcao": funcao_input,
                                "irmao": irmao_input
                            }).execute()
                            st.success("✅ Designação adicionada com sucesso no Supabase!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"Erro ao guardar designação: {err}")
                    else:
                        st.warning("Preencha todos os campos antes de guardar.")

    # PAINEL DE GESTÃO DO ADMINISTRADOR (Barra Lateral)
    if st.session_state["user_role"] == "admin":
        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Aprovar Utilizadores")
        
        try:
            pendentes = supabase.table("usuarios").select("*").eq("status", "pendente").execute()
            if pendentes.data:
                st.sidebar.warning(f"📩 {len(pendentes.data)} pedido(s) pendente(s)!")
                for u in pendentes.data:
                    tel_exib = u.get('telefone') or 'Não informado'
                    st.sidebar.write(f"👤 **{u['nome']}**\n📧 {u['email']}\n📱 {tel_exib}")
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
🗄️ 2. Garantir que criou a tabela escalas no Supabase
Se ainda não executou o comando no Supabase, abra o SQL Editor no Supabase e rode este comando para criar a tabela de escalas e preenchê-la com os dados de Outubro:
create table if not exists escalas (
  id bigint generated by default as identity primary key,
  mes text not null,
  data_texto text not null,
  dia_semana text not null,
  funcao text not null,
  irmao text not null
);

alter table escalas disable row level security;

delete from escalas where mes = '2026-10';

insert into escalas (mes, data_texto, dia_semana, funcao, irmao) values
('2026-10', 'Segunda-feira — 05/10/2026', 'seg', '🗣️ Oração Inicial', 'Lucas Valler'),
('2026-10', 'Segunda-feira — 05/10/2026', 'seg', '🗣️ Oração Final', 'Guerino Bastelli'),
('2026-10', 'Segunda-feira — 05/10/2026', 'seg', '🎤 Microfones', 'Ricardo Maciel / Jamenson Lisboa'),
('2026-10', 'Segunda-feira — 05/10/2026', 'seg', '🚪 Ind. Entrada', 'Adalberto Camargo'),
('2026-10', 'Segunda-feira — 05/10/2026', 'seg', '🏛️ Ind. Auditório', 'Laércio Paulino'),

('2026-10', 'Sábado — 10/10/2026', 'sab', '🗣️ Oração Final', 'Adriano Carbinatto'),
('2026-10', 'Sábado — 10/10/2026', 'sab', '📖 Leitor A Sentinela', 'Jamenson Lisboa'),
('2026-10', 'Sábado — 10/10/2026', 'sab', '🎤 Microfones', 'Gabriel Carbinatto / Gabriel Pereira'),
('2026-10', 'Sábado — 10/10/2026', 'sab', '🚪 Ind. Entrada', 'Uilson Lisboa'),
('2026-10', 'Sábado — 10/10/2026', 'sab', '🏛️ Ind. Auditório', 'Jairo Damasceno'),

('2026-10', 'Segunda-feira — 12/10/2026', 'seg', '🗣️ Oração Inicial', 'Laércio Paulino'),
('2026-10', 'Segunda-feira — 12/10/2026', 'seg', '🗣️ Oração Final', 'Uilson Lisboa'),
('2026-10', 'Segunda-feira — 12/10/2026', 'seg', '🎤 Microfones', 'Ueldson Lisboa / Marcio Silva'),
('2026-10', 'Segunda-feira — 12/10/2026', 'seg', '🚪 Ind. Entrada', 'Lucas Carbinatto'),
('2026-10', 'Segunda-feira — 12/10/2026', 'seg', '🏛️ Ind. Auditório', 'Enio Gomes'),

('2026-10', 'Sábado — 17/10/2026', 'sab', '🗣️ Oração Final', 'Jorge Ramos'),
('2026-10', 'Sábado — 17/10/2026', 'sab', '📖 Leitor A Sentinela', 'Renê Mordente'),
('2026-10', 'Sábado — 17/10/2026', 'sab', '🎤 Microfones', 'Ricardo Maciel / Jamenson Lisboa'),
('2026-10', 'Sábado — 17/10/2026', 'sab', '🚪 Ind. Entrada', 'Jairo Damasceno'),
('2026-10', 'Sábado — 17/10/2026', 'sab', '🏛️ Ind. Auditório', 'Adalberto Camargo'),

('2026-10', 'Segunda-feira — 19/10/2026', 'seg', '🗣️ Oração Inicial', 'Gesaías Vencato'),
('2026-10', 'Segunda-feira — 19/10/2026', 'seg', '🗣️ Oração Final', 'Adalberto Camargo'),
('2026-10', 'Segunda-feira — 19/10/2026', 'seg', '🎤 Microfones', 'Gabriel Pereira / Marcio Silva'),
('2026-10', 'Segunda-feira — 19/10/2026', 'seg', '🚪 Ind. Entrada', 'Marcelo Carrera'),
('2026-10', 'Segunda-feira — 19/10/2026', 'seg', '🏛️ Ind. Auditório', 'Rogério Balista'),

('2026-10', 'Sábado — 24/10/2026', 'sab', '🗣️ Oração Final', 'Delaércio Carneiro'),
('2026-10', 'Sábado — 24/10/2026', 'sab', '📖 Leitor A Sentinela', 'Lucas Carbinatto'),
('2026-10', 'Sábado — 24/10/2026', 'sab', '🎤 Microfones', 'Ueldson Lisboa / Jairo Damasceno'),
('2026-10', 'Sábado — 24/10/2026', 'sab', '🚪 Ind. Entrada', 'Enio Gomes'),
('2026-10', 'Sábado — 24/10/2026', 'sab', '🏛️ Ind. Auditório', 'Marcel Silvério'),

('2026-10', 'Segunda-feira — 26/10/2026', 'seg', '🗣️ Oração Inicial', 'Renê Mordente'),
('2026-10', 'Segunda-feira — 26/10/2026', 'seg', '🗣️ Oração Final', 'Lucas Carbinatto'),
('2026-10', 'Segunda-feira — 26/10/2026', 'seg', '🎤 Microfones', 'Ricardo Maciel / Gabriel Pereira'),
('2026-10', 'Segunda-feira — 26/10/2026', 'seg', '🚪 Ind. Entrada', 'Uilson Lisboa'),
('2026-10', 'Segunda-feira — 26/10/2026', 'seg', '🏛️ Ind. Auditório', 'Jorge Ramos'),

('2026-10', 'Sábado — 31/10/2026', 'sab', '🗣️ Oração Final', 'Samuel Schnetes'),
('2026-10', 'Sábado — 31/10/2026', 'sab', '📖 Leitor A Sentinela', 'Lucas Valler'),
('2026-10', 'Sábado — 31/10/2026', 'sab', '🎤 Microfones', 'Marcio Silva / Jamenson Lisboa'),
('2026-10', 'Sábado — 31/10/2026', 'sab', '🚪 Ind. Entrada', 'Adalberto Camargo'),
('2026-10', 'Sábado — 31/10/202O ecrã ficou em branco devido a uma pequena falha na criação das abas no Streamlit. 

Aqui tem a versão **corrigida e simplificada do `app.py`**, pronta a copiar e colar no GitHub:

---

### 1. Ficheiro `app.py` no GitHub

Substitua todo o conteúdo do `app.py` no GitHub por este código:

```python
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
SUPABASE_KEY = "COLE_AQUI_A_SUA_CHAVE_ANON_DO_SUPABASE"  # <--- COLE A SUA CHAVE ANON AQUI

@st.cache_resource
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = get_supabase()
except Exception as e:
    st.error("Erro ao ligar ao banco de dados Supabase.")

# 3. Estado da Sessão
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None

# --- TELA DE LOGIN / REGISTO ---
if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>🏛️ Portal de Designações Mecânicas</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6B7280;'>Congregação Jardim América</p>", unsafe_allow_html=True)
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_cadastro = st.tabs(["🔑 Entrar na Conta", "📝 Criar Nova Conta"])

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
                            if user.get("status") == "aprovado":
                                st.session_state["logged_in"] = True
                                st.session_state["user_name"] = user["nome"]
                                st.session_state["user_role"] = user["perfil"]
                                st.success(f"Bem-vindo, {user['nome']}!")
                                st.rerun()
                            elif user.get("status") == "pendente":
                                st.warning("⏳ O seu registo ainda está pendente de autorização pelo Administrador.")
                            else:
                                st.error("❌ O seu pedido de acesso não foi aprovado.")
                        else:
                            st.error("E-mail ou palavra-passe incorretos.")
                    except Exception as err:
                        st.error(f"Erro ao verificar conta: {err}")
                else:
                    st.warning("Preencha o e-mail e a palavra-passe.")

        with tab_cadastro:
            st.subheader("Registo de Novo Irmão")
            nome_cad = st.text_input("Nome Completo:")
            email_cad = st.text_input("E-mail:").strip().lower()
            tel_cad = st.text_input("WhatsApp (ex: 5519983035946):").strip()
            senha_cad = st.text_input("Crie uma Palavra-passe:", type="password")

            if st.button("Enviar Pedido de Registo", use_container_width=True):
                if nome_cad and email_cad and senha_cad and tel_cad:
                    try:
                        check = supabase.table("usuarios").select("id").eq("email", email_cad).execute()
                        if check.data:
                            st.error("Este e-mail já está registado no sistema.")
                        else:
                            supabase.table("usuarios").insert({
                                "nome": nome_cad,
                                "email": email_cad,
                                "telefone": tel_cad,
                                "senha": senha_cad,
                                "status": "pendente",
                                "perfil": "irmao"
                            }).execute()
                            st.success("✅ Registo enviado com sucesso! Aguarde a aprovação.")
                    except Exception as err:
                        st.error(f"Erro ao realizar registo: {err}")
                else:
                    st.warning("Preencha todos os campos.")

# --- ÁREA INTERNA LOGADA ---
else:
    st.sidebar.title("🏛️ Jardim América")
    st.sidebar.write(f"👤 **{st.session_state['user_name']}**")
    st.sidebar.caption(f"Perfil: **{st.session_state['user_role'].upper()}**")
    
    if st.sidebar.button("🚪 Terminar Sessão", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["user_name"] = ""
        st.session_state["user_role"] = None
        st.rerun()

    # Buscar meses
    try:
        res_meses = supabase.table("escalas").select("mes").execute()
        meses_disponiveis = sorted(list(set([m["mes"] for m in res_meses.data]))) if res_meses.data else ["2026-10"]
    except Exception:
        meses_disponiveis = ["2026-10"]

    if "2026-10" not in meses_disponiveis:
        meses_disponiveis.insert(0, "2026-10")

    mes_selecionado = st.sidebar.selectbox("📅 Selecionar Mês:", meses_disponiveis, index=0)

    # Buscar dados da escala
    try:
        res_escala = supabase.table("escalas").select("*").eq("mes", mes_selecionado).execute()
        dados_escala = res_escala.data if res_escala.data else []
    except Exception:
        dados_escala = []

    datas_dict = {}
    for item in dados_escala:
        dt = item["data_texto"]
        if dt not in datas_dict:
            datas_dict[dt] = []
        datas_dict[dt].append({"funcao": item["funcao"], "irmao": item["irmao"]})

    # Criar Abas
    if st.session_state["user_role"] == "admin":
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Escala do Mês", "🔍 Procurar por Irmão", "📄 Imprimir PDF", "⚙️ Gerir Escalas"])
    else:
        tab1, tab2, tab3 = st.tabs(["📅 Escala do Mês", "🔍 Procurar por Irmão", "📄 Imprimir PDF"])
        tab4 = None

    with tab1:
        st.subheader(f"📋 Designações Mecânicas — {mes_selecionado}")
        if not datas_dict:
            st.info("Nenhuma escala registada no banco de dados para este mês.")
        else:
            lista_datas = list(datas_dict.keys())
            for i in range(0, len(lista_datas), 2):
                c1, c2 = st.columns(2)
                dt1 = lista_datas[i]
                with c1:
                    st.info(f"🔹 **{dt1}**")
                    for item in datas_dict[dt1]:
                        st.write(f"**{item['funcao']}:** {item['irmao']}")
                
                if i + 1 < len(lista_datas):
                    dt2 = lista_datas[i+1]
                    with c2:
                        st.success(f"🟣 **{dt2}**")
                        for item in datas_dict[dt2]:
                            st.write(f"**{item['funcao']}:** {item['irmao']}")
                st.divider()

    with tab2:
        st.subheader("🔍 Minhas Designações")
        busca = st.text_input("Digite o nome para consultar:", value=st.session_state["user_name"])
        if busca:
            encontrado = False
            for dt, itens in datas_dict.items():
                for item in itens:
                    if busca.lower() in item["irmao"].lower():
                        st.success(f"📅 **{dt}** — **{item['funcao']}:** {item['irmao']}")
                        encontrado = True
            if not encontrado:
                st.warning("Nenhuma designação localizada para este nome.")

    with tab3:
        st.subheader("📄 Documento Oficial para Impressão")
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

    if tab4 is not None:
        with tab4:
            st.subheader("⚙️ Cadastrar Nova Designação")
            with st.form("form_nova_designacao"):
                c_mes, c_dia = st.columns(2)
                mes_input = c_mes.text_input("Mês (Ano-Mês):", value="2026-11")
                data_texto_input = c_dia.text_input("Data Formatada:", value="Segunda-feira — 02/11/2026")
                
                c_func, c_irm = st.columns(2)
                funcao_input = c_func.selectbox("Função:", [
                    "🗣️ Oração Inicial", "🗣️ Oração Final", "📖 Leitor A Sentinela", 
                    "🎤 Microfones", "🚪 Ind. Entrada", "🏛️ Ind. Auditório"
                ])
                irmao_input = c_irm.text_input("Nome do Irmão:")
                dia_sem_input = st.selectbox("Tipo de Reunião:", ["seg", "sab"], format_func=lambda x: "Segunda-feira" if x == "seg" else "Sábado")
                
                if st.form_submit_button("➕ Adicionar à Escala", type="primary", use_container_width=True):
                    if mes_input and data_texto_input and irmao_input:
                        try:
                            supabase.table("escalas").insert({
                                "mes": mes_input,
                                "data_texto": data_texto_input,
                                "dia_semana": dia_sem_input,
                                "funcao": funcao_input,
                                "irmao": irmao_input
                            }).execute()
                            st.success("✅ Designação adicionada!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"Erro: {err}")

    # Painel do Admin na Barra Lateral
    if st.session_state["user_role"] == "admin":
        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Aprovar Utilizadores")
        try:
            pendentes = supabase.table("usuarios").select("*").eq("status", "pendente").execute()
            if pendentes.data:
                for u in pendentes.data:
                    st.sidebar.write(f"👤 **{u['nome']}** ({u.get('telefone', 'Sem tel')})")
                    c_ap, c_rec = st.sidebar.columns(2)
                    if c_ap.button("✅", key=f"ap_{u['id']}"):
                        supabase.table("usuarios").update({"status": "aprovado"}).eq("id", u["id"]).execute()
                        st.rerun()
                    if c_rec.button("❌", key=f"rec_{u['id']}"):
                        supabase.table("usuarios").update({"status": "recusado"}).eq("id", u["id"]).execute()
                        st.rerun()
        except Exception:
            pass
