import streamlit as st
import pandas as pd
import calculos_estoque
import io

def renderizar_tela_volumetria(database, integracao):
    st.subheader("📊 Indicadores de Volumetria & Paletização")
    st.caption("Cálculo parametrizado de cubagem, folga operacional e ocupação de porta-paletes.")

    # --- CONTROLES DE PARÂMETROS NA BARRA LATERAL ---
    with st.sidebar:
        st.divider()
        st.subheader("⚙️ Parâmetros do Palete")
        
        alt_vao = st.number_input(
            "Altura do Vão (m):", 
            min_value=0.50, max_value=3.00, value=1.50, step=0.05,
            help="Altura total do vão livre na estrutura porta-paletes."
        )
        
        alt_madeira = st.number_input(
            "Altura da Madeira (m):", 
            min_value=0.00, max_value=0.30, value=0.15, step=0.01,
            help="Altura do estrado de madeira a ser descontada da carga."
        )
        
        fator_ocupacao = st.slider(
            "Fator de Eficiência / Margem (%):", 
            min_value=50, max_value=100, value=90, step=5,
            help="Margem para absorver espaços vazios entre caixas (90% = 10% de folga)."
        )

    # 1. Carrega parâmetros dos produtos do banco
    try:
        produtos_cadastrados = database.obter_lista_produtos_com_medidas()
    except Exception:
        produtos_cadastrados = pd.DataFrame(columns=['SKU', 'Nome', 'Pack_Caixa', 'Comp_m', 'Larg_m', 'Alt_m'])

    # 2. Botão para acionar busca de saldo na API
    col_btn, _ = st.columns([2, 2])
    with col_btn:
        if st.button("🔄 Buscar Estoque Atualizado da API"):
            with st.spinner("Consultando API e calculando saldos..."):
                st.session_state.dados_estoque_api = integracao.obter_estoque_completo_api(database)
                st.success("Dados de estoque atualizados!")

    df_estoque = st.session_state.get('dados_estoque_api', pd.DataFrame())

    if df_estoque.empty:
        st.info("💡 Clique no botão acima para carregar o estoque da API.")
        return

    # 3. Filtro por Base / Depósito
    if 'Base' in df_estoque.columns:
        bases_disponiveis = ["Todas"] + sorted(list(df_estoque['Base'].unique()))
        base_selecionada = st.selectbox("Filtrar por Base / Unidade:", bases_disponiveis)
        if base_selecionada != "Todas":
            df_estoque = df_estoque[df_estoque['Base'] == base_selecionada]

    # 4. Processamento dos Cálculos Matematizados
    df_resultado, kpis = calculos_estoque.calcular_volumetria_paletes(
        df_estoque=df_estoque, 
        df_produtos=produtos_cadastrados,
        altura_vao_m=alt_vao,
        altura_madeira_m=alt_madeira,
        fator_ocupacao_pct=fator_ocupacao
    )

    # 5. Cartões de Indicadores Chave (KPIs)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Total Peças", f"{kpis['total_pecas']:,}".replace(",", "."))
    col2.metric("🏷️ Caixas (Packs)", f"{kpis['total_caixas']:,}".replace(",", "."))
    col3.metric("📐 Volumetria Total", f"{kpis['total_m3']} m³")
    col4.metric(
        "🏗️ Posições Paletes", 
        f"{kpis['total_paletes']} PL", 
        help=f"Volume útil calculado por palete: {kpis['vol_util_palete']} m³"
    )

    st.divider()

    # 6. Tabela Detalhada dos Resultados
    st.write("### 📋 Detalhamento da Ocupação por SKU")
    
    colunas_visiveis = ['SKU', 'Nome', 'Saldo_Pecas', 'Total_Caixas', 'Vol_Total_m3', 'Paletes_Estimados']
    colunas_existentes = [c for c in colunas_visiveis if c in df_resultado.columns]
    
    st.dataframe(
        df_resultado[colunas_existentes].rename(columns={
            'Saldo_Pecas': 'Saldo (Peças)',
            'Total_Caixas': 'Total Caixas',
            'Vol_Total_m3': 'Volume (m³)',
            'Paletes_Estimados': 'Est. Paletes'
        }),
        width="stretch"
    )

    # 7. Botão de Exportação para Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_resultado.to_excel(writer, sheet_name='Volumetria_Estoque', index=False)
    
    st.download_button(
        label="📥 Baixar Relatório Completo em Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name="relatorio_volumetria_paletes.xlsx",
        mime="application/vnd.ms-excel"
    )