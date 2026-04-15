from fpdf import FPDF
import qrcode
import io

# Dicionário de Produtos
PRODUTOS = {
    "AT9902": "MOCHILA BAG 99 FOOD",
    "LK0467": "CHEST BAG POLIESTER P/ BIKE",
    "ECT9905": "BAG STREET POLIESTER 300 DIGITAL - 99 FOOD",
    "LK169906": "MOCHILA STREET PRETA - 99 FOOD"
}

def extrair_prefixo(sku):
    import re
    match = re.match(r"([a-zA-Z]+)", sku)
    return match.group(1) if match else "ID"

def gerar_pdf_lote(lista_dados):
    """
    Gera um PDF onde cada página é uma etiqueta de 100mm x 50mm.
    lista_dados deve ser uma lista de dicionários ou tuplas com (qrcode, sku, desc)
    """
    # 'L' = Landscape (Deitado), 'mm' = Milímetros, format = (Altura, Largura)
    pdf = FPDF(orientation='L', unit='mm', format=(50, 100))
    pdf.set_margin(0)
    pdf.set_auto_page_break(False)

    for item in lista_dados:
        cod_qr, sku, desc = item
        pdf.add_page()
        
        # 1. Gerar imagem do QR Code em memória
        qr = qrcode.QRCode(version=1, box_size=10, border=0)
        qr.add_data(cod_qr)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        
        img_buffer = io.BytesIO()
        img_qr.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # 2. Desenhar no PDF
        # QR Code (40x40mm)
        pdf.image(img_buffer, x=5, y=5, w=40, h=40)
        
        # SKU (Texto em destaque)
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_xy(48, 10)
        pdf.cell(45, 10, txt=sku, ln=True)
        
        # Descrição (Texto com quebra automática)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_xy(48, 20)
        pdf.multi_cell(w=47, h=6, txt=desc)
        
        # Código em texto pequeno abaixo do QR
        pdf.set_font("Helvetica", "", 8)
        pdf.text(x=5, y=47, txt=cod_qr)
        
    # Adicionamos o bytes() para converter o formato e o Streamlit aceitar
    return bytes(pdf.output())