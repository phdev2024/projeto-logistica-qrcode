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
            status TEXT DEFAULT 'Pendente'
        )
    ''')
    conn.commit()
    conn.close()

def salvar_etiqueta(qrcode, sku, pedido):
    conn = sqlite3.connect('logistica.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO etiquetas (qrcode, sku, pedido) VALUES (?, ?, ?)", 
                   (qrcode, sku, pedido))
    conn.commit()
    conn.close()

def buscar_ultimo_num(prefixo):
    conn = sqlite3.connect('logistica.db')
    cursor = conn.cursor()
    # Busca o maior número sequencial para aquele prefixo específico
    cursor.execute("SELECT qrcode FROM etiquetas WHERE qrcode LIKE ? ORDER BY qrcode DESC LIMIT 1", (f"{prefixo}%",))
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        # Extrai apenas os números do final do QR Code
        return int(''.join(filter(str.isdigit, resultado[0])))
    return 0

def atualizar_status_expedicao(qrcode):
    conn = sqlite3.connect('logistica.db')
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM etiquetas WHERE qrcode = ?", (qrcode,))
    item = cursor.fetchone()
    
    if item:
        if item[0] == 'Expedido':
            conn.close()
            return "⚠️ Este item já foi expedido anteriormente!"
        cursor.execute("UPDATE etiquetas SET status = 'Expedido' WHERE qrcode = ?", (qrcode,))
        conn.commit()
        conn.close()
        return f"✅ Item {qrcode} expedido com sucesso!"
    conn.close()
    return "❌ Erro: Código não encontrado no banco de dados."

def listar_etiquetas():
    conn = sqlite3.connect('logistica.db')
    cursor = conn.cursor()
    cursor.execute("SELECT qrcode, sku, pedido, data_criacao, status FROM etiquetas ORDER BY data_criacao DESC")
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