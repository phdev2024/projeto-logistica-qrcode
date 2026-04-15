import streamlit as st
import database
import logic
import pandas as pd

database.criar_tabelas()

st.set_page_config(page_title="Sistema Logístico Paulo", page_icon="📦")
st.title("📦 Gestão de Etiquetas & Expedição")

aba = st.sidebar.radio("Navegação:", ["Gerar Etiquetas", "Expedição", "Consultar Banco"])

if aba == "Gerar Etiquetas":
    st.subheader("🛠️ Emissão de Lote de Etiquetas")
    sku_selecionado = st.selectbox("Selecione o SKU", list(logic.PRODUTOS.keys()))
    descricao = logic.PRODUTOS[sku_selecionado]
    
    col1, col2 = st.columns(2)
    with col1:
        pedido = st.text_input("Número do Pedido")
    with col2:
        qtd = st.number_input("Quantidade de Etiquetas", min_value=1, value=1, step=1)

    if st.button("Gerar Lote em PDF"):
        if not pedido:
            st.warning("Por favor, informe o número do pedido.")
        else:
            prefixo = logic.extrair_prefixo(sku_selecionado)
            ultimo_valor = database.buscar_ultimo_num(prefixo)
            
            dados_lote = []
            
            # Criar os dados de cada etiqueta e salvar no banco
            for i in range(1, int(qtd) + 1):
                novo_codigo = f"{prefixo}{str(ultimo_valor + i).zfill(10)}"
                database.salvar_etiqueta(novo_codigo, sku_selecionado, pedido)
                dados_lote.append((novo_codigo, sku_selecionado, descricao))
            
            # Gerar o PDF único com todas as etiquetas
            pdf_bytes = logic.gerar_pdf_lote(dados_lote)
            
            st.success(f"✅ {len(dados_lote)} etiquetas geradas e salvas no banco!")
            
            st.download_button(
                label="📥 Baixar Lote em PDF",
                data=pdf_bytes,
                file_name=f"lote_pedido_{pedido}.pdf",
                mime="application/pdf"
            )

elif aba == "Expedição":
    st.subheader("🚚 Módulo de Expedição")
    codigo_lido = st.text_input("Bipe o QR Code aqui", key="scan")
    if codigo_lido:
        resultado = database.atualizar_status_expedicao(codigo_lido)
        if "Sucesso" in resultado:
            st.success(resultado)
        else:
            st.error(resultado)

elif aba == "Consultar Banco":
    st.subheader("🔍 Histórico de Movimentação")
    dados = database.listar_etiquetas()
    if dados:
        df = pd.DataFrame(dados, columns=["QR Code", "SKU", "Pedido", "Data Criação", "Status"])
        st.dataframe(df, use_container_width=True)