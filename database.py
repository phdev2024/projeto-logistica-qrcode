import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import streamlit as st

# --- CONFIGURAÇÃO DA CONEXÃO ---
# Coloque aqui o nome exato do seu arquivo JSON
NOME_ARQUIVO_JSON = "credenciais.json" 
# Coloque o nome exato da sua planilha no Drive
NOME_PLANILHA = "DB_Qrcode" 

def conectar():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # 1. Tenta primeiro usar as Secrets (Modo Nuvem/Empresa)
    if "gcp_service_account" in st.secrets:
        try:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            return client.open(NOME_PLANILHA).worksheet("etiquetas")
        except Exception as e:
            st.error(f"Erro ao conectar via Secrets: {e}")

    # 2. Se não houver Secrets, tenta o arquivo local (Seu PC de casa)
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(NOME_ARQUIVO_JSON, scope)
        client = gspread.authorize(creds)
        return client.open(NOME_PLANILHA).worksheet("etiquetas")
    except FileNotFoundError:
        st.error("Erro: Arquivo JSON não encontrado localmente e Secrets não configuradas.")
        raise

def criar_tabelas():
    # No Sheets não "criamos tabelas", mas podemos verificar a conexão
    try:
        conectar()
        print("Conectado ao Google Sheets com sucesso!")
    except Exception as e:
        print(f"Erro ao conectar: {e}")

def salvar_etiqueta(qrcode, sku, pedido, usuario):
    sheet = conectar()
    data_criacao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    # Adiciona a linha na planilha: qrcode, sku, pedido, data, status, criador, expedidor
    sheet.append_row([qrcode, sku, pedido, data_criacao, "Pendente", usuario, ""])

def buscar_ultimo_num(prefixo):
    sheet = conectar()
    dados = sheet.get_all_records()
    if not dados:
        return 0
    
    # Filtra os QRCodes que começam com o prefixo e pega o maior número
    numeros = []
    for linha in dados:
        qr = str(linha.get('qrcode', ''))
        if qr.startswith(prefixo):
            # Extrai apenas os números do QR Code
            num = ''.join(filter(str.isdigit, qr))
            if num: numeros.append(int(num))
    
    return max(numeros) if numeros else 0

def atualizar_status_expedicao(qrcode, usuario):
    sheet = conectar()
    try:
        # Procura o código na coluna A (qrcode)
        celula = sheet.find(qrcode)
        if celula:
            # Coluna E é Status (5), Coluna G é User Expedição (7)
            sheet.update_cell(celula.row, 5, "Expedido")
            sheet.update_cell(celula.row, 7, usuario)
            return f"✅ Item {qrcode} expedido por {usuario}!"
        return "❌ Erro: Código não encontrado na planilha."
    except:
        return "❌ Erro ao acessar a planilha."

def listar_etiquetas():
    sheet = conectar()
    # Retorna uma lista de tuplas para manter a compatibilidade com o app.py atual
    dados = sheet.get_all_records()
    lista_formatada = []
    for d in dados:
        lista_formatada.append((
            d.get('qrcode'), d.get('sku'), d.get('pedido'), 
            d.get('data_criacao'), d.get('status'), 
            d.get('user_criacao'), d.get('user_expedicao')
        ))
    return lista_formatada

def buscar_etiquetas_por_pedido(pedido):
    sheet = conectar()
    dados = sheet.get_all_records()
    return [(d['qrcode'], d['sku'], d['status']) for d in dados if str(d['pedido']) == str(pedido)]