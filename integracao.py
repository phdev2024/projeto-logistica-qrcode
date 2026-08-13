import requests

# =====================================================================
# CONFIGURAÇÕES DA API DA EMPRESA
# =====================================================================
URL_API = "https://intranet.profilelog.com.br/99pedidos/api/api.php"
TOKEN_AUTENTICACAO = "Bearer f7d29a1b-3c5e-4a8d-9b2c-1e8f4a7b9d0e"

def testar_conexao_api():
    """
    Mantida para testes rápidos na barra lateral.
    """
    headers = {
        "Authorization": TOKEN_AUTENTICACAO,
        "Content-Type": "application/json"
    }
    params = {"idBase": "2"}
    
    try:
        resposta = requests.get(URL_API, headers=headers, params=params, timeout=10)
        if resposta.status_code == 200:
            return {"sucesso": True, "dados": resposta.json()}
        return {"sucesso": False, "erro": f"Erro HTTP {resposta.status_code}"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def obter_produtos_unicos_api():
    """
    Busca os produtos na API e remove duplicidades de SKU de forma inteligente.
    Retorna um dicionário formato { "SKU": "Nome do Produto" }.
    """
    headers = {
        "Authorization": TOKEN_AUTENTICACAO,
        "Content-Type": "application/json"
    }
    params = {"idBase": "1"}
    
    try:
        resposta = requests.get(URL_API, headers=headers, params=params, timeout=10)
        if resposta.status_code != 200:
            return None
            
        dados_brutos = resposta.json()
        
        # Acessa a lista de produtos que está dentro da chave "data"
        lista_produtos = dados_brutos.get("data", [])
        
        # Dicionário auxiliar para eliminar duplicados
        produtos_filtrados = {}
        
        for prod in lista_produtos:
            sku = str(prod.get("SKU", "")).strip()
            nome = str(prod.get("Nome", "")).strip()
            
            # Só adiciona se o SKU e Nome forem válidos
            if sku and nome:
                # Se o SKU se repetir na resposta da API, ele apenas substitui
                # no dicionário, garantindo unicidade por SKU.
                produtos_filtrados[sku] = nome
                
        return produtos_filtrados
        
    except Exception as e:
        print(f"Erro ao buscar e filtrar produtos da API: {e}")
        return None