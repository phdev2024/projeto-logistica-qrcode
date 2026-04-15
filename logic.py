from PIL import Image, ImageDraw, ImageFont
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

def gerar_etiqueta_img(codigo_qr, sku, descricao):
    # Criamos uma imagem branca (proporção 10x5cm)
    largura, altura = 800, 400
    imagem = Image.new('RGB', (largura, altura), color='white')
    draw = ImageDraw.Draw(imagem)
    
    # 1. Gerar o QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(codigo_qr)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    # Redimensionar QR Code para ficar proporcional e colar
    img_qr = img_qr.resize((300, 300))
    imagem.paste(img_qr, (30, 30))
    
    # 2. Configurar Fontes (Tenta Arial, se não tiver usa a padrão)
    try:
        fonte_sku = ImageFont.truetype("arial.ttf", 60)
        fonte_desc = ImageFont.truetype("arial.ttf", 35)
        fonte_mini = ImageFont.truetype("arial.ttf", 20)
    except:
        fonte_sku = ImageFont.load_default()
        fonte_desc = ImageFont.load_default()
        fonte_mini = ImageFont.load_default()

    # 3. Escrever as informações
    draw.text((360, 60), sku, fill="black", font=fonte_sku)
    
    # Quebra de linha simples para a descrição (máximo 22 caracteres por linha)
    import textwrap
    linhas = textwrap.wrap(descricao, width=22)
    y_text = 140
    for linha in linhas:
        draw.text((360, y_text), linha, fill="black", font=fonte_desc)
        y_text += 45
        
    draw.text((30, 340), codigo_qr, fill="black", font=fonte_mini)

    # Converter para bytes para o Streamlit
    buf = io.BytesIO()
    imagem.save(buf, format='PNG')
    return buf.getvalue()