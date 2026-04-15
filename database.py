import sqlite3

def criar_tabelas():
    conn = sqlite3.connect('logistica.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS etiquetas (
            qrcode TEXT PRIMARY KEY,
            sku TEXT,
            pedido TEXT,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Pendente',
            user_criacao TEXT,
            user_expedicao TEXT
        )
    ''')
    conn.commit()
    conn.close()

def salvar_etiqueta(qrcode, sku, pedido, usuario):
    conn = sqlite3.connect('logistica.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO etiquetas (qrcode, sku, pedido, user_criacao) VALUES (?, ?, ?, ?)", 
                   (qrcode, sku, pedido, usuario))
    conn.commit()
    conn.close()

def buscar_ultimo_num(prefixo):
    conn = sqlite3.connect('logistica.db')
    cursor = conn.cursor()
    cursor.execute("SELECT qrcode FROM etiquetas WHERE qrcode LIKE ? ORDER BY qrcode DESC LIMIT 1", (f"{prefixo}%",))
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        return int(''.join(filter(str.isdigit, resultado[0])))
    return 0

def atualizar_status_expedicao(qrcode, usuario):
    conn = sqlite3.connect('logistica.db')
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM etiquetas WHERE qrcode = ?", (qrcode,))
    item = cursor.fetchone()
    
    if item:
        if item[0] == 'Expedido':
            conn.close()
            return "⚠️ Este item já foi expedido!"
        cursor.execute("UPDATE etiquetas SET status = 'Expedido', user_expedicao = ? WHERE qrcode = ?", (usuario, qrcode))
        conn.commit()
        conn.close()
        return f"✅ Item {qrcode} expedido por {usuario}!"
    conn.close()
    return "❌ Erro: Código não encontrado."

def listar_etiquetas():
    conn = sqlite3.connect('logistica.db')
    cursor = conn.cursor()
    # Adicionamos os usuários na listagem
    cursor.execute("SELECT qrcode, sku, pedido, data_criacao, status, user_criacao, user_expedicao FROM etiquetas ORDER BY data_criacao DESC")
    dados = cursor.fetchall()
    conn.close()
    return dados

def buscar_etiquetas_por_pedido(pedido):
    conn = sqlite3.connect('logistica.db')
    cursor = conn.cursor()
    cursor.execute("SELECT qrcode, sku, status FROM etiquetas WHERE pedido = ?", (pedido,))
    dados = cursor.fetchall()
    conn.close()
    return dados