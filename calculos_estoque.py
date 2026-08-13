import pandas as pd
import math

def calcular_volumetria_paletes(df_estoque, df_produtos, volume_palete_m3=1.80):
    """
    Recebe o DataFrame de estoque atual e o DataFrame de parâmetros de produtos.
    Aplica as regras matemáticas de conversão para Caixas, Volume (m³) e Paletes.
    """
    if df_estoque.empty:
        return pd.DataFrame(), {"total_m3": 0, "total_paletes": 0, "total_caixas": 0}

    # Garante padronização das chaves para o cruzamento (Merge)
    df_estoque['SKU'] = df_estoque['SKU'].astype(str).str.strip()
    df_produtos['SKU'] = df_produtos['SKU'].astype(str).str.strip()

    # Cruzamento dos dados de estoque com o cadastro de medidas de produtos
    df_merged = pd.merge(df_estoque, df_produtos, on='SKU', how='left')

    # Preenchimento de valores nulos para evitar erros em itens não cadastrados
    df_merged['Pack_Caixa'] = pd.to_numeric(df_merged['Pack_Caixa'], errors='coerce').fillna(1)
    df_merged['Comp_m'] = pd.to_numeric(df_merged['Comp_m'], errors='coerce').fillna(0)
    df_merged['Larg_m'] = pd.to_numeric(df_merged['Larg_m'], errors='coerce').fillna(0)
    df_merged['Alt_m'] = pd.to_numeric(df_merged['Alt_m'], errors='coerce').fillna(0)
    df_merged['Saldo_Pecas'] = pd.to_numeric(df_merged['Saldo_Pecas'], errors='coerce').fillna(0)

    # 1. Cálculo de Caixas Master (Packs)
    df_merged['Total_Caixas'] = df_merged['Saldo_Pecas'] / df_merged['Pack_Caixa']
    df_merged['Total_Caixas'] = df_merged['Total_Caixas'].apply(lambda x: math.ceil(x) if x > 0 else 0)

    # 2. Volume Unitário da Caixa (m³)
    df_merged['Vol_Caixa_m3'] = df_merged['Comp_m'] * df_merged['Larg_m'] * df_merged['Alt_m']

    # 3. Volume Total em Estoque (m³)
    df_merged['Vol_Total_m3'] = df_merged['Total_Caixas'] * df_merged['Vol_Caixa_m3']

    # 4. Estimativa de Posições Palete (Consolidação física)
    df_merged['Paletes_Estimados'] = df_merged['Vol_Total_m3'] / volume_palete_m3
    df_merged['Paletes_Estimados'] = df_merged['Paletes_Estimados'].apply(lambda x: math.ceil(x) if x > 0 else 0)

    # Resumo Geral dos Indicadores
    kpis = {
        "total_pecas": int(df_merged['Saldo_Pecas'].sum()),
        "total_caixas": int(df_merged['Total_Caixas'].sum()),
        "total_m3": round(df_merged['Vol_Total_m3'].sum(), 2),
        "total_paletes": int(df_merged['Paletes_Estimados'].sum())
    }

    return df_merged, kpis