from fpdf import FPDF
import qrcode
import io
import re

PRODUTOS = {
    "AT9902": "MOCHILA BAG 99 FOOD",
    "LK0467": "CHEST BAG POLIESTER P/ BIKE",
    "ECT9905": "BAG STREET POLIESTER 300 DIGITAL - 99 FOOD",
    "LK169906": "MOCHILA STREET PRETA - 99 FOOD",
    "LK249904IMP": "MOCHILA BAG 99 FOOD QRCODE COSTAS"
}

def extrair_prefixo(sku):
    match = re.match(r"([a-zA-Z]+)", sku)
    return match.group(1) if match else "ID"

def gerar_pdf_lote(lista_dados):
    # Formato Etiqueta 100x50mm
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
        pdf.cell(45, 10, txt=sku, ln=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_xy(48, 20)
        pdf.multi_cell(w=47, h=6, txt=desc)
        pdf.set_font("Helvetica", "", 8)
        pdf.text(x=5, y=47, txt=cod_qr)
        
    return bytes(pdf.output())

def gerar_relatorio_conferencia(pedido, lista_dados):
    # Formato Relatório A4
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
        pdf.cell(50, 10, cod_qr, border=1)
        pdf.cell(40, 10, sku, border=1)
        desc_curta = desc[:38] + "..." if len(desc) > 38 else desc
        pdf.cell(85, 10, desc_curta, border=1)
        pdf.cell(15, 10, "[  ]", border=1, ln=True, align='C')
        
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 10, "Relatório gerado automaticamente pelo Sistema Logístico Paulo", align='R')
    
    return bytes(pdf.output())