import os
import sqlite3
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import streamlit as st
import pandas as pd

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
def conectar_google(nome_aba="etiquetas"):
    """
    Tenta realizar a conexão com a API do Google Sheets de duas formas:
    1º Pelas Secrets do Streamlit Cloud (Configuração de produção na nuvem)
    2º Pelo arquivo 'credenciais.json' local (Configuração de produção na sua máquina)
    Permite passar opcionalmente qual aba queremos abrir (padrão é 'etiquetas').
    """
    client = None
    
    # Método A: Tentando ler as Secrets do Streamlit (Modo Nuvem)
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
        client = gspread.authorize(creds)

    # Método B: Tentando ler o arquivo JSON local
    elif os.path.exists(NOME_ARQUIVO_JSON):
        creds = ServiceAccountCredentials.from_json_keyfile_name(NOME_ARQUIVO_JSON, SCOPE)
        client = gspread.authorize(creds)
    
    if client:
        # Tenta abrir a planilha e depois a aba selecionada
        planilha = client.open(NOME_PLANILHA)
        try:
            return planilha.worksheet(nome_aba)
        except gspread.exceptions.WorksheetNotFound:
            # Se a aba não existir, nós criamos ela automaticamente!
            if nome_aba == "Produtos":
                return planilha.add_worksheet(title="Produtos", rows="1000", cols="2")
            raise
            
    # Se não houver nenhum dos dois, dispara um erro
    raise FileNotFoundError("Nenhuma credencial do Google (JSON ou Secrets) foi encontrada.")


def conectar_sqlite():
    """
    Conecta ao banco SQLite local 'banco_teste.db'.
    Garante também que as tabelas necessárias sejam criadas localmente.
    """
    conn = sqlite3.connect(BANCO_LOCAL_SQLITE)
    cursor = conn.cursor()
    
    # Criamos a tabela de etiquetas usando exatamente as mesmas colunas da planilha do Google
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
    
    # NOVA TABELA: Tabela local de produtos para guardar a sincronização da API
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos_api (
            sku TEXT PRIMARY KEY,
            nome TEXT NOT NULL
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
    Vasculha as etiquetas existentes com o mesmo prefixo para descobrir qual o maior número sequencial.
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
    """
    try:
        # Tenta no Google Sheets
        sheet = conectar_google()
        celula = sheet.find(qrcode)
        if celula:
            sheet.update_cell(celula.row, 5, "Expedido")
            sheet.update_cell(celula.row, 7, usuario)
            return f"✅ Item {qrcode} expedido por {usuario}! (Salvo na Planilha Oficial)"
        return "❌ Erro: Código não encontrado na planilha oficial."
    except Exception as e:
        # Se der erro de rede, atualiza no SQLite local
        print(f"⚠️ Modificando status no SQLite devido a erro de conexão: {e}")
        conn = conectar_sqlite()
        cursor = conn.cursor()
        
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
    """
    try:
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
        print(f"⚠️ Listando etiquetas a partir do SQLite local devido a: {e}")
        conn = conectar_sqlite()
        cursor = conn.cursor()
        cursor.execute("SELECT qrcode, sku, pedido, data_criacao, status, user_criacao, user_expedicao FROM etiquetas")
        dados_sqlite = cursor.fetchall()
        conn.close()
        return dados_sqlite


def buscar_etiquetas_por_pedido(pedido):
    """
    Filtra todas as etiquetas associadas a um número de pedido específico.
    """
    try:
        sheet = conectar_google()
        dados = sheet.get_all_records()
        return [(d['qrcode'], d['sku'], d['status']) for d in dados if str(d['pedido']) == str(pedido)]
    except Exception as e:
        print(f"⚠️ Buscando pedido '{pedido}' no SQLite devido a: {e}")
        conn = conectar_sqlite()
        cursor = conn.cursor()
        cursor.execute("SELECT qrcode, sku, status FROM etiquetas WHERE pedido = ?", (str(pedido),))
        dados_sqlite = cursor.fetchall()
        conn.close()
        return dados_sqlite


# =====================================================================
# 4. NOVAS FUNÇÕES PARA GESTÃO DE PRODUTOS SINCRONIZADOS DA API
# =====================================================================

def salvar_produtos_sincronizados(produtos_dict):
    """
    Sincroniza produtos novos vindos da API preservando as medidas (Comp_m, Larg_m, Alt_m, Pack_Caixa)
    e quaisquer outras colunas preenchidas manualmente no Google Sheets.
    """
    try:
        aba = conectar_google(nome_aba="Produtos")
        dados_existentes = aba.get_all_values()
        
        # Se a aba estiver completamente vazia, cria o cabeçalho padrão completo
        if not dados_existentes:
            cabecalho = ["SKU", "Nome", "Comp_m", "Larg_m", "Alt_m", "Pack_Caixa"]
            linhas = [cabecalho]
            for sku, nome in produtos_dict.items():
                linhas.append([sku, nome, "", "", "", ""])
            aba.update("A1", linhas)
            print("✅ Catálogo inicial criado com sucesso no Google Sheets!")
            return True

        cabecalho = dados_existentes[0]
        linhas_atuais = dados_existentes[1:]

        # Identifica as posições das colunas SKU e Nome
        idx_sku = cabecalho.index("SKU") if "SKU" in cabecalho else 0
        idx_nome = cabecalho.index("Nome") if "Nome" in cabecalho else 1

        # Mapeia linhas existentes pelo SKU
        mapa_linhas = {}
        for idx, linha in enumerate(linhas_atuais):
            # Garante que a linha tenha o tamanho exato do cabeçalho
            while len(linha) < len(cabecalho):
                linha.append("")
            
            sku_existente = str(linha[idx_sku]).strip()
            if sku_existente:
                mapa_linhas[sku_existente] = linha

        # Atualiza ou insere novos produtos
        for sku_novo, nome_novo in produtos_dict.items():
            sku_formatado = str(sku_novo).strip()
            
            if sku_formatado in mapa_linhas:
                # SKU já existe: atualiza apenas a descrição, mantendo medidas intactas
                mapa_linhas[sku_formatado][idx_nome] = nome_novo
            else:
                # SKU novo da API: cria nova linha mantendo colunas de medidas vazias
                nova_linha = [""] * len(cabecalho)
                nova_linha[idx_sku] = sku_formatado
                nova_linha[idx_nome] = nome_novo
                mapa_linhas[sku_formatado] = nova_linha

        # Monta a matriz final consolidada
        matriz_final = [cabecalho] + list(mapa_linhas.values())

        # Atualiza o Google Sheets com o conjunto completo de dados
        aba.update("A1", matriz_final)
        print("✅ Produtos sincronizados com sucesso preservando todas as medidas!")
        return True

    except Exception as e:
        print(f"⚠️ Falha ao salvar produtos no Sheets ({e}). Atualizando SQLite local...")
        try:
            conectar_sqlite().close()
            conn = sqlite3.connect(BANCO_LOCAL_SQLITE)
            cursor = conn.cursor()
            
            dados_para_salvar = [(sku, nome) for sku, nome in produtos_dict.items()]
            cursor.executemany("""
                INSERT OR REPLACE INTO produtos_api (sku, nome)
                VALUES (?, ?)
            """, dados_para_salvar)
            
            conn.commit()
            conn.close()
            print("✅ Produtos sincronizados no SQLite local!")
            return True
        except Exception as err:
            st.error(f"Erro crítico ao salvar produtos localmente: {err}")
            return False

@st.cache_data(ttl=600)
def obter_lista_produtos():
    """
    Busca os produtos cadastrados no Google Sheets ou no SQLite local.
    Retorna um dicionário { SKU: Nome } para abastecer o dropdown do app.py.
    """
    try:
        # Tenta puxar do Google Sheets
        aba = conectar_google(nome_aba="Produtos")
        dados = aba.get_all_values()
        
        produtos = {}
        # Ignora a primeira linha (cabeçalho)
        for linha in dados[1:]:
            if len(linha) >= 2:
                sku, nome = linha[0].strip(), linha[1].strip()
                if sku and nome:
                    produtos[sku] = nome
        return produtos
        
    except Exception as e:
        # Se falhar, busca do SQLite local
        print(f"⚠️ Lendo produtos do banco SQLite local devido a: {e}")
        produtos = {}
        try:
            conn = sqlite3.connect(BANCO_LOCAL_SQLITE)
            cursor = conn.cursor()
            cursor.execute("SELECT sku, nome FROM produtos_api")
            for sku, nome in cursor.fetchall():
                produtos[sku] = nome
            conn.close()
        except Exception as err:
            print(f"Erro ao ler tabela produtos_api local: {err}")
        return produtos

def obter_lista_produtos_com_medidas():
    """
    Busca a lista de produtos com as colunas de cubagem e pack.
    Retorna um DataFrame do Pandas.
    """
    try:
        aba = conectar_google(nome_aba="Produtos")
        dados = aba.get_all_values()
        
        if len(dados) <= 1:
            return pd.DataFrame(columns=['SKU', 'Nome', 'Pack_Caixa', 'Comp_m', 'Larg_m', 'Alt_m'])
            
        # Pega o cabeçalho e os dados
        cabecalho = [str(c).strip() for c in dados[0]]
        linhas = dados[1:]
        
        df = pd.DataFrame(linhas, columns=cabecalho)
        return df
        
    except Exception as e:
        print(f"⚠️ Lendo medidas do SQLite local devido a: {e}")
        # Retorna um DataFrame vazio padronizado para não travar
        return pd.DataFrame(columns=['SKU', 'Nome', 'Pack_Caixa', 'Comp_m', 'Larg_m', 'Alt_m'])

def obter_cadastro_bases():
    """
    Lê a aba 'Bases' na planilha oficial do Google Sheets.
    Retorna um dicionário formato { "1": "Matriz - Jandira", "2": "Filial - SP" }.
    """
    try:
        # Tenta conectar explicitamente na aba 'Bases'
        aba = conectar_google(nome_aba="Bases")
        dados = aba.get_all_values()
        
        bases = {}
        # Se a aba tiver linhas (pelo menos o cabeçalho e 1 dado)
        if len(dados) > 1:
            for linha in dados[1:]: # Pula a linha 0 (cabeçalho)
                if len(linha) >= 2:
                    id_b = str(linha[0]).strip()
                    nome_b = str(linha[1]).strip()
                    if id_b and nome_b:
                        bases[id_b] = nome_b
        return bases
    except Exception as e:
        print(f"⚠️ Erro ao ler aba Bases no Sheets: {e}")
        return {}