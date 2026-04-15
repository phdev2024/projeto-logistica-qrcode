import streamlit as st
import database
import logic
import pandas as pd

# Inicia o banco ao abrir o app
database.criar_tabelas()

st.set_page_config(page_title="Logística - Etiquetas Zebra", page_icon="📦")

st.title("📦 Sistema de Etiquetas Logísticas")
st.markdown("---")

st.sidebar.header("Menu Principal")
aba = st.sidebar.radio("Navegação:", ["Gerar Etiquetas", "Consultar Banco"])

if aba == "Gerar Etiquetas":
    st.subheader("🛠️ Configurar Impressão")
    
    sku_selecionado = st.selectbox("Selecione o SKU do Produto", list(logic.PRODUTOS.keys()))
    descricao = logic.PRODUTOS[sku_selecionado]
    st.info(f"**Item selecionado:** {descricao}")
    
    col1, col2 = st.columns(2)
    with col1:
        pedido = st.text_input("Número do Pedido", placeholder="Ex: 4500123")
    with col2:
        qtd = st.number_input("Quantidade de Volumes", min_value=1, value=1, step=1)

    if st.button("Gerar e Registrar Etiquetas"):
        if not pedido:
            st.warning("⚠️ Informe o número do pedido.")
        else:
            prefixo = logic.extrair_prefixo(sku_selecionado)
            
            # BUSCA O ÚLTIMO NÚMERO REGISTRADO NO BANCO PARA ESSE PREFIXO
            ultimo_valor = database.buscar_ultimo_num(prefixo)
            
            conteudo_zpl = ""
            progresso = st.progress(0)
            
            for i in range(1, int(qtd) + 1):
                # O novo número será o último que estava no banco + i
                novo_sequencial = ultimo_valor + i
                num_seq_formatado = str(novo_sequencial).zfill(10)
                qrcode_final = f"{prefixo}{num_seq_formatado}"
                
                database.salvar_etiqueta(qrcode_final, sku_selecionado, pedido)
                conteudo_zpl += logic.formatar_zpl(qrcode_final, sku_selecionado, descricao)
                progresso.progress(i / int(qtd))
            
            st.success(f"✅ {qtd} etiquetas geradas! Próximo número disponível: {prefixo}{str(ultimo_valor + qtd + 1).zfill(10)}")
            
            st.download_button(
                label="📥 Baixar Arquivo ZPL",
                data=conteudo_zpl,
                file_name=f"pedido_{pedido}_etiquetas.zpl",
                mime="text/plain"
            )

elif aba == "Consultar Banco":
    st.subheader("🔍 Histórico de Geração (Rastreabilidade)")
    dados = database.listar_etiquetas()
    if dados:
        df = pd.DataFrame(dados, columns=["QR Code", "SKU Produto", "Pedido", "Data de Criação", "Status"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("O banco de dados está vazio.")