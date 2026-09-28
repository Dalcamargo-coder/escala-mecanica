import os
import datetime
from supabase import create_client

# Configurações do Supabase
SUPABASE_URL = "https://jwstginzuimrbvvavrlv.supabase.co"
SUPABASE_KEY = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp3c3RnaW56dWltcmJ2dmF2cmx2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA2MjIwNDgsImV4cCI6MjEwNjE5ODA0OH0.XNLaxpWCElIntlXWS6_moHHCnzkTXUXBhcFoRx6K93M", "COLE_AQUI_A_SUA_CHAVE_ANON_DO_SUPABASE")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Escala de Outubro 2026 (Exemplo de dados)
semanas = [
    {
        "data_seg": "Segunda-feira — 05/10/2026",
        "seg": {"Oração Inicial": "Marcel Silvério", "Oração Final": "Adalberto Camargo", "Microfones": "Adalberto Camargo / Laércio Paulino", "Indicador de Entrada": "Laércio Paulino", "Indicador de Auditório": "Marcel Silvério"},
        "data_sab": "Sábado — 10/10/2026",
        "sab": {"Oração Final": "Gabriel Pereira", "Leitor A Sentinela": "Jamenson Lisboa", "Microfones": "Gabriel Pereira / Jairo Damasceno", "Indicador de Entrada": "Jairo Damasceno", "Indicador de Auditório": "Ricardo Maciel"}
    },
    {
        "data_seg": "Segunda-feira — 12/10/2026",
        "seg": {"Oração Inicial": "Ueldson Lisboa", "Oração Final": "Uilson Lisboa", "Microfones": "Ueldson Lisboa / Uilson Lisboa", "Indicador de Entrada": "Marcio Silva", "Indicador de Auditório": "Enio Gomes"},
        "data_sab": "Sábado — 17/10/2026",
        "sab": {"Oração Final": "Marcelo Carrera", "Leitor A Sentinela": "Renê Mordente", "Microfones": "Marcelo Carrera / Samuel Schnetes", "Indicador de Entrada": "Samuel Schnetes", "Indicador de Auditório": "Gesaías Vencato"}
    }
]

def buscar_telefone_irmao(nome_busca):
    """Procura no Supabase o número de telefone registado do irmão."""
    try:
        res = supabase.table("usuarios").select("nome, telefone").eq("status", "aprovado").execute()
        for u in res.data:
            if u.get("nome") and u["nome"].strip().lower() in nome_busca.strip().lower():
                return u.get("telefone")
    except Exception as e:
        print(f"Erro ao consultar Supabase: {e}")
    return None

def gerar_avisos_proxima_reuniao():
    """Identifica as designações e prepara a lista de avisos por WhatsApp."""
    avisos = []
    
    # Exemplo: pega as designações da primeira semana registrada
    primeira_semana = semanas[0]
    
    print(f"=== GERANDO AVISOS PARA: {primeira_semana['data_seg']} ===")
    for funcao, irmao in primeira_semana["seg"].items():
        # Lidar com funções duplas (ex: "Irmão A / Irmão B")
        nomes = [n.strip() for n in irmao.split("/")]
        for nome in nomes:
            tel = buscar_telefone_irmao(nome)
            msg = (
                f"Olá, irmão *{nome}*! 👋\n\n"
                f"Lembrete da sua designação na *Congregação Jardim América*:\n"
                f"📅 *Data:* {primeira_semana['data_seg']}\n"
                f"📋 *Designação:* {funcao}\n\n"
                f"Se precisar de fazer uma troca, informe o superintendente da reunião com antecedência. Obrigado pelo apoio!"
            )
            avisos.append({"nome": nome, "telefone": tel, "mensagem": msg})
            
    return avisos

if __name__ == "__main__":
    lista_avisos = gerar_avisos_proxima_reuniao()
    print(f"\nTotal de avisos gerados: {len(lista_avisos)}\n")
    for item in lista_avisos:
        tel_status = item['telefone'] if item['telefone'] else "⚠️ Telefone não cadastrado"
        print(f"👤 {item['nome']} | 📱 {tel_status}")
        print(f"💬 Mensagem:\n{item['mensagem']}\n{'-'*40}")
