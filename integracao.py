import requests
import streamlit as st
import pandas as pd

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

def obter_estoque_completo_api(database=None):
    """
    Varre todas as bases cadastradas no Google Sheets e traduz os IDs para os nomes reais.
    """
    headers = {
        "Authorization": TOKEN_AUTENTICACAO,
        "Content-Type": "application/json"
    }
    
    # 1. Busca o mapeamento de bases cadastradas no Sheets
    mapeamento_bases = {}
    if database:
        try:
            # Pega o dicionário { "1": "Matriz", "2": "Filial" }
            raw_bases = database.obter_cadastro_bases()
            # Padroniza todas as chaves como texto limpo
            mapeamento_bases = {str(k).strip(): str(v).strip() for k, v in raw_bases.items()}
            print(f"📊 Bases encontradas na Planilha: {mapeamento_bases}")
        except Exception as e:
            print(f"⚠️ Aviso ao ler aba Bases: {e}")

    # Se a planilha não retornar nada, faz fallback de 1 a 15 para não travar
    if not mapeamento_bases:
        print("⚠️ Dicionário de bases vazio. Usando números genéricos de 1 a 15.")
        mapeamento_bases = {str(i): f"Base {i}" for i in range(1, 16)}

    todos_os_saldos = []

    # 2. Varre CADA base cadastrada
    for base_id, nome_base in mapeamento_bases.items():
        params = {"idBase": str(base_id)}
        try:
            resposta = requests.get(URL_API, headers=headers, params=params, timeout=8)
            if resposta.status_code == 200:
                dados_brutos = resposta.json()
                lista_itens = dados_brutos.get("data", [])
                
                # Se a API retornar dados para essa base
                for item in lista_itens:
                    sku = str(item.get("SKU", "")).strip()
                    nome = str(item.get("Nome", "")).strip()
                    saldo = item.get("Saldo", 0)
                    
                    if sku and saldo > 0:
                        todos_os_saldos.append({
                            "SKU": sku,
                            "Nome": nome,
                            "Saldo_Pecas": saldo,
                            "Base": nome_base  # Aplica o nome vindo da planilha
                        })
        except Exception as e:
            print(f"❌ Erro ao consultar a Base {base_id} ({nome_base}): {e}")
            
    return pd.DataFrame(todos_os_saldos)