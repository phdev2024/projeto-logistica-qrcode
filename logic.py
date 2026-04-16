import pandas as pd
import os
import re
from fpdf import FPDF
import qrcode
import io

def carregar_produtos():
    caminho_arquivo = 'produtos.csv'
    if os.path.exists(caminho_arquivo):
        try:
            # Tenta ler tratando acentuação e descobrindo se é vírgula ou ponto e vírgula
            df = pd.read_csv(caminho_arquivo, sep=None, engine='python', encoding='ISO-8859-1')
            
            # Limpa os nomes das colunas (tira espaços e coloca em minúsculo)
            df.columns = [c.strip().lower() for c in df.columns]
            
            # Verifica se as colunas necessárias existem (sku e nome)
            if 'sku' in df.columns and 'nome' in df.columns:
                return pd.Series(df.nome.values, index=df.sku.values).to_dict()
            else:
                # Se os nomes na planilha estiverem diferentes, tentamos pegar pelas duas primeiras colunas
                return pd.Series(df.iloc[:, 1].values, index=df.iloc[:, 0].values).to_dict()
        except Exception as e:
            print(f"Erro ao ler CSV: {e}")
            return {"ERRO": "Verifique o arquivo produtos.csv"}
    
    # Padrão caso o arquivo não exista
    return {"AT9902": "MOCHILA BAG 99 FOOD"}

# Carrega a lista de 90+ itens para ser usada pelo app.py
PRODUTOS = carregar_produtos()

def extrair_prefixo(sku):
    match = re.match(r"([a-zA-Z]+)", str(sku))
    return match.group(1) if match else "ID"

def gerar_pdf_lote(lista_dados):
    pdf = FPDF(orientation='L', unit='mm', format=(50, 100))
    pdf.set_margin(0)
    pdf.set_auto_page_break(False)

    for item in lista_dados:
        cod_qr, sku, desc = item
        pdf.add_page()
        
        qr = qrcode.QRCode(version=1, box_size=10, border=0)
        qr.add_data(cod_qr)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        
        img_buffer = io.BytesIO()
        img_qr.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        pdf.image(img_buffer, x=5, y=5, w=40, h=40)
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_xy(48, 10)
        pdf.cell(45, 10, txt=str(sku), ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_xy(48, 20)
        pdf.multi_cell(w=47, h=6, txt=str(desc))
        pdf.set_font("Helvetica", "", 8)
        pdf.text(x=5, y=47, txt=str(cod_qr))
        
    return bytes(pdf.output())

def gerar_relatorio_conferencia(pedido, lista_dados):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 20, f"Checklist de Expedição - Pedido: {pedido}", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(50, 10, "Código QR", border=1, align='C')
    pdf.cell(40, 10, "SKU", border=1, align='C')
    pdf.cell(85, 10, "Descrição", border=1, align='C')
    pdf.cell(15, 10, "Conf.", border=1, ln=True, align='C')
    pdf.set_font("Helvetica", "", 10)
    for cod_qr, sku, desc in lista_dados:
        pdf.cell(50, 10, str(cod_qr), border=1)
        pdf.cell(40, 10, str(sku), border=1)
        desc_str = str(desc)
        desc_curta = desc_str[:38] + "..." if len(desc_str) > 38 else desc_str
        pdf.cell(85, 10, desc_curta, border=1)
        pdf.cell(15, 10, "[  ]", border=1, ln=True, align='C')
    return bytes(pdf.output())