import pandas as pd
import math

def limpar_e_converter_numero(serie, valor_padrao=0.0):
    """
    Trata strings vindas do Google Sheets com vírgulas brasileiras (ex: '0,45'),
    espaços ou erros de fórmula e converte com segurança para float.
    """
    return (
        serie.astype(str)
        .str.replace(",", ".", regex=False)
        .str.strip()
        .apply(pd.to_numeric, errors="coerce")
        .fillna(valor_padrao)
    )

def calcular_volumetria_paletes(df_estoque, df_produtos, volume_palete_m3=1.80):
    """
    Recebe o estoque e o cadastro de produtos com medidas.
    Calcula Packs/Caixas, Volume Total (m³) e Estimativa de Ocupação de Paletes.
    """
    if df_estoque.empty:
        return pd.DataFrame(), {"total_pecas": 0, "total_caixas": 0, "total_m3": 0, "total_paletes": 0}

    # 1. Padroniza a chave SKU para garantir o cruzamento perfeito
    df_estoque['SKU'] = df_estoque['SKU'].astype(str).str.strip().str.upper()
    df_produtos['SKU'] = df_produtos['SKU'].astype(str).str.strip().str.upper()

    # 2. Cruza os dados do estoque com as medidas do cadastro
    df_merged = pd.merge(df_estoque, df_produtos, on='SKU', how='left')

    # 3. Limpeza e conversão robusta de tipos (tratando vírgulas e nulos)
    df_merged['Pack_Caixa'] = limpar_e_converter_numero(df_merged.get('Pack_Caixa', pd.Series()), valor_padrao=1.0)
    df_merged['Comp_m'] = limpar_e_converter_numero(df_merged.get('Comp_m', pd.Series()), valor_padrao=0.0)
    df_merged['Larg_m'] = limpar_e_converter_numero(df_merged.get('Larg_m', pd.Series()), valor_padrao=0.0)
    df_merged['Alt_m'] = limpar_e_converter_numero(df_merged.get('Alt_m', pd.Series()), valor_padrao=0.0)
    df_merged['Saldo_Pecas'] = limpar_e_converter_numero(df_merged.get('Saldo_Pecas', pd.Series()), valor_padrao=0.0)

    # Garante que Pack_Caixa nunca seja menor ou igual a zero para evitar divisão por zero
    df_merged['Pack_Caixa'] = df_merged['Pack_Caixa'].apply(lambda x: x if x > 0 else 1.0)

    # 4. Cálculo de Caixas Master (Packs)
    df_merged['Total_Caixas'] = (df_merged['Saldo_Pecas'] / df_merged['Pack_Caixa']).apply(lambda x: math.ceil(x) if x > 0 else 0)

    # 5. Volume Unitário da Caixa (m³)
    df_merged['Vol_Caixa_m3'] = df_merged['Comp_m'] * df_merged['Larg_m'] * df_merged['Alt_m']

    # 6. Volume Total em Estoque (m³)
    df_merged['Vol_Total_m3'] = (df_merged['Total_Caixas'] * df_merged['Vol_Caixa_m3']).round(3)

    # 7. Estimativa de Posições Palete (Porta-Paletes Padrão 1,80 m³)
    df_merged['Paletes_Estimados'] = (df_merged['Vol_Total_m3'] / volume_palete_m3).apply(lambda x: math.ceil(x) if x > 0 else 0)

    # Resumo Geral dos KPIs para os cartões no topo da tela
    kpis = {
        "total_pecas": int(df_merged['Saldo_Pecas'].sum()),
        "total_caixas": int(df_merged['Total_Caixas'].sum()),
        "total_m3": round(float(df_merged['Vol_Total_m3'].sum()), 2),
        "total_paletes": int(df_merged['Paletes_Estimados'].sum())
    }

    return df_merged, kpis