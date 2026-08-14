import pandas as pd
import math

def limpar_e_converter_numero(serie, valor_padrao=0.0):
    """
    Trata números com vírgula ou vindos em formato de texto e converte para float seguro.
    """
    return (
        serie.astype(str)
        .str.replace(",", ".", regex=False)
        .str.strip()
        .apply(pd.to_numeric, errors="coerce")
        .fillna(valor_padrao)
    )

def calcular_volumetria_paletes(df_estoque, df_produtos, altura_vao_m=1.50, altura_madeira_m=0.15, fator_ocupacao_pct=90):
    """
    Calcula Packs/Caixas, Volume (m³) e Paletes considerando descontos de altura de madeira
    e margem de segurança de arrumação (fator de ocupação).
    """
    if df_estoque.empty:
        return pd.DataFrame(), {
            "total_pecas": 0, "total_caixas": 0, "total_m3": 0, 
            "total_paletes": 0, "vol_util_palete": 0.0
        }

    # 1. Padroniza chaves de cruzamento
    df_estoque['SKU'] = df_estoque['SKU'].astype(str).str.strip().str.upper()
    df_produtos['SKU'] = df_produtos['SKU'].astype(str).str.strip().str.upper()

    # 2. Merge do Estoque com Cadastro de Medidas
    df_merged = pd.merge(df_estoque, df_produtos, on='SKU', how='left')

    # 3. Limpeza dos Dados
    df_merged['Pack_Caixa'] = limpar_e_converter_numero(df_merged.get('Pack_Caixa', pd.Series()), valor_padrao=1.0)
    df_merged['Comp_m'] = limpar_e_converter_numero(df_merged.get('Comp_m', pd.Series()), valor_padrao=0.0)
    df_merged['Larg_m'] = limpar_e_converter_numero(df_merged.get('Larg_m', pd.Series()), valor_padrao=0.0)
    df_merged['Alt_m'] = limpar_e_converter_numero(df_merged.get('Alt_m', pd.Series()), valor_padrao=0.0)
    df_merged['Saldo_Pecas'] = limpar_e_converter_numero(df_merged.get('Saldo_Pecas', pd.Series()), valor_padrao=0.0)

    df_merged['Pack_Caixa'] = df_merged['Pack_Caixa'].apply(lambda x: x if x > 0 else 1.0)

    # 4. Cálculo de Caixas Master
    df_merged['Total_Caixas'] = (df_merged['Saldo_Pecas'] / df_merged['Pack_Caixa']).apply(lambda x: math.ceil(x) if x > 0 else 0)

    # 5. Volume Unitário da Caixa (m³)
    df_merged['Vol_Caixa_m3'] = df_merged['Comp_m'] * df_merged['Larg_m'] * df_merged['Alt_m']

    # 6. Volume Total em Estoque (m³)
    df_merged['Vol_Total_m3'] = (df_merged['Total_Caixas'] * df_merged['Vol_Caixa_m3']).round(3)

    # 7. Cálculo do Volume Útil Real do Palete (Porta-Palete PBR)
    # Altura útil de caixas = Altura total do vão - Altura do estrado de madeira
    altura_util = max(0.1, altura_vao_m - altura_madeira_m)
    
    # Base PBR padrão = 1,00m x 1,20m
    volume_bruto_palete = 1.00 * 1.20 * altura_util
    
    # Aplica o Fator de Ocupação / Margem de Segurança (ex: 90% = 0.90)
    vol_util_palete = round(volume_bruto_palete * (fator_ocupacao_pct / 100.0), 3)

    # 8. Estimativa de Paletes com arredondamento seguro
    df_merged['Paletes_Estimados'] = (df_merged['Vol_Total_m3'] / vol_util_palete).apply(lambda x: math.ceil(x) if x > 0 else 0)

    # Resumo Geral dos KPIs
    kpis = {
        "total_pecas": int(df_merged['Saldo_Pecas'].sum()),
        "total_caixas": int(df_merged['Total_Caixas'].sum()),
        "total_m3": round(float(df_merged['Vol_Total_m3'].sum()), 2),
        "total_paletes": int(df_merged['Paletes_Estimados'].sum()),
        "vol_util_palete": vol_util_palete
    }

    return df_merged, kpis