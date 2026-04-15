import sqlite3
import re
from datetime import datetime

def conectar():
    return sqlite3.connect('logistica.db')

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()
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
    # Pega data e hora local do computador (Brasília)
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
    """Busca o maior número já usado para um prefixo (ex: LK)"""
    conn = conectar()
    cursor = conn.cursor()
    # Busca o qrcode que começa com o prefixo e pega o maior valor
    cursor.execute("SELECT qrcode FROM etiquetas WHERE qrcode LIKE ? ORDER BY qrcode DESC LIMIT 1", (f"{prefixo}%",))
    resultado = cursor.fetchone()
    conn.close()
    
    if resultado:
        # Extrai apenas os números do código (ex: LK0000000005 -> 5)
        apenas_numeros = re.sub(r'\D', '', resultado[0])
        return int(apenas_numeros)
    return 0

def listar_etiquetas():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('SELECT qrcode, produto_cod, pedido, data_criacao, status FROM etiquetas ORDER BY id DESC')
    dados = cursor.fetchall()
    conn.close()
    return dados