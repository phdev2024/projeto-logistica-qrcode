import requests
import streamlit as st

# =====================================================================
# CONFIGURAÇÕES SEGURAS DA API (LÊ DAS SECRETS DO STREAMLIT)
# =====================================================================
if "api_empresa" in st.secrets:
    URL_API = st.secrets["api_empresa"]["url"]
    TOKEN_AUTENTICACAO = st.secrets["api_empresa"]["token"]
else:
    # Fallback para desenvolvimento local
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
        lista_produtos = dados_brutos.get("data", [])
        produtos_filtrados = {}
        
        for prod in lista_produtos:
            sku = str(prod.get("SKU", "")).strip()
            nome = str(prod.get("Nome", "")).strip()
            
            if sku and nome:
                produtos_filtrados[sku] = nome
                
        return produtos_filtrados
        
    except Exception as e:
        print(f"Erro ao buscar e filtrar produtos da API: {e}")
        return None