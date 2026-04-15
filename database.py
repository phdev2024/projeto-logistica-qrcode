import sqlite3
import re
from datetime import datetime

def conectar():
    return sqlite3.connect('logistica.db')

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()
    # Criamos a tabela com as colunas que precisamos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS etiquetas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            qrcode TEXT UNIQUE,
            produto_cod TEXT,
            pedido TEXT,
            data_criacao TEXT,
            status TEXT DEFAULT 'Pendente'
        )
    ''')
    conn.commit()
    conn.close()

def salvar_etiqueta(qrcode, produto, pedido):
    conn = conectar()
    cursor = conn.cursor()
    agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    try:
        cursor.execute('''
            INSERT INTO etiquetas (qrcode, produto_cod, pedido, data_criacao)
            VALUES (?, ?, ?, ?)
        ''', (qrcode, produto, pedido, agora))
        conn.commit()
    except sqlite3.IntegrityError:
        pass 
    finally:
        conn.close()

def buscar_ultimo_num(prefixo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT qrcode FROM etiquetas WHERE qrcode LIKE ? ORDER BY qrcode DESC LIMIT 1", (f"{prefixo}%",))
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        apenas_numeros = re.sub(r'\D', '', resultado[0])
        return int(apenas_numeros)
    return 0

# NOVO: Função para dar baixa na expedição
def atualizar_status_expedicao(qrcode):
    conn = conectar()
    cursor = conn.cursor()
    agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    
    # 1. Verifica se o QR Code existe
    cursor.execute("SELECT status FROM etiquetas WHERE qrcode = ?", (qrcode,))
    resultado = cursor.fetchone()
    
    if resultado:
        if resultado[0] == 'Expedido':
            conn.close()
            return "Aviso: Este item já saiu!"
        
        # 2. Se existe e está pendente, muda para Expedido
        cursor.execute("UPDATE etiquetas SET status = 'Expedido' WHERE qrcode = ?", (qrcode,))
        conn.commit()
        conn.close()
        return "Sucesso: Item expedido!"
    
    conn.close()
    return "Erro: Código não encontrado."

def listar_etiquetas():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('SELECT qrcode, produto_cod, pedido, data_criacao, status FROM etiquetas ORDER BY id DESC')
    dados = cursor.fetchall()
    conn.close()
    return dados