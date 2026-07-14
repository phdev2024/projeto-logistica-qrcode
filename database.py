import os
import sqlite3
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import streamlit as st

# =====================================================================
# 1. CONFIGURAÇÕES GERAIS
# =====================================================================
NOME_ARQUIVO_JSON = "credenciais.json" 
NOME_PLANILHA = "DB_Qrcode"  # Banco oficial no Google Drive da empresa

# Nome do arquivo local que será gerado apenas na sua máquina de testes
BANCO_LOCAL_SQLITE = "banco_teste.db"

# Escopo padrão exigido pelo Google para acessar planilhas e drive
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# =====================================================================
# 2. SISTEMA INTELIGENTE DE CONEXÃO
# =====================================================================
def conectar_google():
    """
    Tenta realizar a conexão com a API do Google Sheets de duas formas:
    1º Pelas Secrets do Streamlit Cloud (Configuração de produção na nuvem)
    2º Pelo arquivo 'credenciais.json' local (Configuração de produção na sua máquina)
    """
    # Método A: Tentando ler as Secrets do Streamlit (Modo Nuvem)
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
        client = gspread.authorize(creds)
        return client.open(NOME_PLANILHA).worksheet("etiquetas")

    # Método B: Tentando ler o arquivo JSON local
    if os.path.exists(NOME_ARQUIVO_JSON):
        creds = ServiceAccountCredentials.from_json_keyfile_name(NOME_ARQUIVO_JSON, SCOPE)
        client = gspread.authorize(creds)
        return client.open(NOME_PLANILHA).worksheet("etiquetas")
    
    # Se não houver nenhum dos dois, dispara um erro que será capturado pelas funções abaixo
    raise FileNotFoundError("Nenhuma credencial do Google (JSON ou Secrets) foi encontrada.")


def conectar_sqlite():
    """
    Conecta ao banco SQLite local 'banco_teste.db'.
    Se o arquivo não existir, o próprio Python o cria automaticamente.
    Garante também que a tabela 'etiquetas' com as colunas idênticas às
    do Google Sheets seja criada.
    """
    conn = sqlite3.connect(BANCO_LOCAL_SQLITE)
    cursor = conn.cursor()
    
    # Criamos a tabela usando exatamente as mesmas colunas da planilha do Google
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etiquetas (
            qrcode TEXT PRIMARY KEY,
            sku TEXT,
            pedido TEXT,
            data_criacao TEXT,
            status TEXT,
            user_criacao TEXT,
            user_expedicao TEXT
        )
    """)
    conn.commit()
    return conn

# =====================================================================
# 3. FUNÇÕES COMPATÍVEIS COM O APP.PY
# =====================================================================

def criar_tabelas():
    """
    Chamada na inicialização do 'app.py'.
    Valida a conexão com o Google e garante que a tabela SQLite esteja pronta.
    """
    try:
        # Se conseguir conectar ao Google, ótimo
        conectar_google()
        print("✅ Conectado com sucesso ao Google Sheets oficial!")
    except Exception as e:
        # Se der erro (ex: falta de internet ou bloqueio de rede), prepara o SQLite
        print(f"⚠️ Conexão com Google Sheets falhou ({e}). Inicializando banco SQLite de testes local.")
        conectar_sqlite().close()


def salvar_lote_etiquetas(lista_de_linhas):
    """
    Recebe uma lista de linhas (listas) e insere todas de uma vez.
    Tenta primeiro o Google Sheets (em lote para evitar bloqueio por quota/erro 429).
    Se falhar, insere tudo de uma vez no SQLite local.
    """
    try:
        # Tenta salvar na nuvem
        sheet = conectar_google()
        sheet.append_rows(lista_de_linhas)
        return True
    except Exception as e:
        # Se a internet/Google falhar, usamos o plano B: SQLite
        print(f"⚠️ Falha de rede ao salvar lote ({e}). Salvando dados no banco de testes local...")
        try:
            conn = conectar_sqlite()
            cursor = conn.cursor()
            
            # Mapeia as linhas e faz o insert em massa no banco local
            cursor.executemany("""
                INSERT OR REPLACE INTO etiquetas (qrcode, sku, pedido, data_criacao, status, user_criacao, user_expedicao)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, lista_de_linhas)
            
            conn.commit()
            conn.close()
            return True
        except Exception as err:
            st.error(f"Erro crítico ao salvar dados localmente no SQLite: {err}")
            return False


def salvar_etiqueta(qrcode, sku, pedido, usuario):
    """
    Salva uma etiqueta de forma individual (mantida por compatibilidade no app).
    """
    data_criacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    linha = [qrcode, sku, pedido, data_criacao, "Pendente", usuario, ""]
    
    try:
        # Tenta no Google
        sheet = conectar_google()
        sheet.append_row(linha)
    except Exception as e:
        # Fallback para o SQLite
        print(f"⚠️ Salvando etiqueta única localmente devido a: {e}")
        conn = conectar_sqlite()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO etiquetas (qrcode, sku, pedido, data_criacao, status, user_criacao, user_expedicao)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, linha)
        conn.commit()
        conn.close()


def buscar_ultimo_num(prefixo):
    """
    Vasculha as etiquetas existentes com o mesmo prefixo para descobrir qual o maior número sequencial
    e não duplicar códigos na criação do QR code.
    """
    dados = []
    try:
        # Tenta puxar do Google Sheets
        sheet = conectar_google()
        dados_sheets = sheet.get_all_records()
        dados = dados_sheets
    except Exception as e:
        # Se der erro, busca do SQLite local
        print(f"⚠️ Buscando último número do banco SQLite devido a: {e}")
        conn = conectar_sqlite()
        cursor = conn.cursor()
        cursor.execute("SELECT qrcode FROM etiquetas")
        # Converte a consulta em uma lista de dicionários para se comportar como o Google Sheets (.get_all_records())
        dados = [{"qrcode": r[0]} for r in cursor.fetchall()]
        conn.close()

    if not dados:
        return 0
    
    numeros = []
    for linha in dados:
        qr = str(linha.get('qrcode', ''))
        if qr.startswith(prefixo):
            num = ''.join(filter(str.isdigit, qr))
            if num: 
                numeros.append(int(num))
    
    return max(numeros) if numeros else 0


def atualizar_status_expedicao(qrcode, usuario):
    """
    Muda o status do QR code lido para 'Expedido' e insere o usuário que bipou.
    Funciona tanto no Google quanto localmente no SQLite.
    """
    try:
        # Tenta no Google Sheets
        sheet = conectar_google()
        celula = sheet.find(qrcode)
        if celula:
            # Coluna E (5) = Status, Coluna G (7) = User Expedição
            sheet.update_cell(celula.row, 5, "Expedido")
            sheet.update_cell(celula.row, 7, usuario)
            return f"✅ Item {qrcode} expedido por {usuario}! (Salvo na Planilha Oficial)"
        return "❌ Erro: Código não encontrado na planilha oficial."
    except Exception as e:
        # Se der erro de rede, atualiza no SQLite local
        print(f"⚠️ Modificando status no SQLite devido a erro de conexão: {e}")
        conn = conectar_sqlite()
        cursor = conn.cursor()
        
        # Verifica se o código realmente existe no SQLite
        cursor.execute("SELECT 1 FROM etiquetas WHERE qrcode = ?", (qrcode,))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE etiquetas 
                SET status = 'Expedido', user_expedicao = ? 
                WHERE qrcode = ?
            """, (usuario, qrcode))
            conn.commit()
            conn.close()
            return f"✅ Item {qrcode} expedido por {usuario}! (Salvo no Banco de Teste Local)"
        conn.close()
        return "❌ Erro: Código não encontrado no banco de testes local."


def listar_etiquetas():
    """
    Retorna todas as etiquetas cadastradas.
    Mantém a formatação de lista de tuplas exigida pela tabela no 'app.py'.
    """
    try:
        # Tenta carregar os dados reais do Sheets
        sheet = conectar_google()
        dados = sheet.get_all_records()
        lista_formatada = []
        for d in dados:
            lista_formatada.append((
                d.get('qrcode'), d.get('sku'), d.get('pedido'), 
                d.get('data_criacao'), d.get('status'), 
                d.get('user_criacao'), d.get('user_expedicao')
            ))
        return lista_formatada
    except Exception as e:
        # Se falhar (bloqueio de rede), traz do SQLite local
        print(f"⚠️ Listando etiquetas a partir do SQLite local devido a: {e}")
        conn = conectar_sqlite()
        cursor = conn.cursor()
        cursor.execute("SELECT qrcode, sku, pedido, data_criacao, status, user_criacao, user_expedicao FROM etiquetas")
        dados_sqlite = cursor.fetchall()
        conn.close()
        # Já retorna no formato exato que o pandas DataFrame espera no app.py
        return dados_sqlite


def buscar_etiquetas_por_pedido(pedido):
    """
    Filtra todas as etiquetas associadas a um número de pedido específico.
    Usado para gerar o Checklist de Conferência e Reimpressão de lotes.
    """
    try:
        # Tenta filtrar no Google Sheets
        sheet = conectar_google()
        dados = sheet.get_all_records()
        return [(d['qrcode'], d['sku'], d['status']) for d in dados if str(d['pedido']) == str(pedido)]
    except Exception as e:
        # Se falhar, busca e filtra do SQLite local
        print(f"⚠️ Buscando pedido '{pedido}' no SQLite devido a: {e}")
        conn = conectar_sqlite()
        cursor = conn.cursor()
        cursor.execute("SELECT qrcode, sku, status FROM etiquetas WHERE pedido = ?", (str(pedido),))
        dados_sqlite = cursor.fetchall()
        conn.close()
        return dados_sqlite