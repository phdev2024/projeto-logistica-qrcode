import re

# Sua lista de produtos oficial
PRODUTOS = {
    "AT9902": "MOCHILA BAG 99 FOOD",
    "ECT9902": "MOCHILA BAG 99 FOOD",
    "ECT9904": "MOCHILA BAG 99 FOOD QRCODE",
    "ECT9905": "MOCHILA BAG 99 FOOD QRCODE COSTAS",
    "LK0467": "CHEST BAG POLIESTER P/ BIKE",
    "LK169905": "MOCHILA BAG 99 FOOD QRCODE COSTAS",
    "LK169906": "BAG STREET POLIESTER 300 DIGITAL - 99 FOOD",
    "LK9901": "MOCHILA BAG 99 FOOD",
    "LK9902": "MOCHILA BAG 99 FOOD",
    "LK9903": "MOCHILA BAG PEDE 99 QRCODE",
    "LK9904": "MOCHILA BAG 99 FOOD QRCODE",
    "PRC0099": "MOCHILA 45L AMARELA 99 FOOD ALUMINIZADA"
}

def extrair_prefixo(sku):
    """Extrai as letras iniciais do SKU para o QR Code."""
    match = re.match(r"([a-zA-Z]+)", sku)
    return match.group(1).upper() if match else "QR"

def formatar_zpl(qrcode, sku, descricao):
    """Gera o comando ZPL para a etiqueta Zebra."""
    desc_curta = descricao[:30]
    
    zpl = f"""
^XA
^FO100,50^BQN,2,10^FDQA,{qrcode}^FS
^FO100,280^A0N,30,30^FD{qrcode}^FS
^FO100,320^A0N,20,20^FDSKU: {sku}^FS
^FO100,350^A0N,20,20^FD{desc_curta}^FS
^XZ
"""
    return zpl