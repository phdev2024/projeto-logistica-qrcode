import streamlit as st
import database
import logic
import pandas as pd

database.criar_tabelas()

st.set_page_config(page_title="Logística - Etiquetas", page_icon="📦")
st.title("📦 Sistema de Etiquetas Logísticas")

aba = st.sidebar.radio("Navegação:", ["Gerar Etiquetas", "Expedição", "Consultar Banco"])

if aba == "Gerar Etiquetas":
    st.subheader("🛠️ Gerar Etiqueta Visual")
    sku_selecionado = st.selectbox("Selecione o SKU", list(logic.PRODUTOS.keys()))
    descricao = logic.PRODUTOS[sku_selecionado]
    
    col1, col2 = st.columns(2)
    with col1:
        pedido = st.text_input("Número do Pedido")
    with col2:
        qtd = st.number_input("Quantidade (será gerado o primeiro código)", min_value=1, value=1)

    if st.button("Gerar Prévia e Salvar"):
        if not pedido:
            st.warning("Informe o pedido.")
        else:
            prefixo = logic.extrair_prefixo(sku_selecionado)
            ultimo_valor = database.buscar_ultimo_num(prefixo)
            
            # Geramos a primeira do lote para prévia
            proximo_num = ultimo_valor + 1
            qrcode_final = f"{prefixo}{str(proximo_num).zfill(10)}"
            
            # Salva no banco
            database.salvar_etiqueta(qrcode_final, sku_selecionado, pedido)
            
            # Gera a imagem
            img_data = logic.gerar_etiqueta_img(qrcode_final, sku_selecionado, descricao)
            
            st.image(img_data, caption="Prévia da Etiqueta Gerada", use_container_width=True)
            
            st.download_button(
                label="📥 Baixar Etiqueta para Imprimir",
                data=img_data,
                file_name=f"etiqueta_{qrcode_final}.png",
                mime="image/png"
            )
            st.success(f"Registrado no banco como {qrcode_final}")

elif aba == "Expedição":
    st.subheader("🚚 Módulo de Expedição")
    codigo_lido = st.text_input("Bipe o QR Code aqui", key="scan")
    if codigo_lido:
        resultado = database.atualizar_status_expedicao(codigo_lido)
        if "Sucesso" in resultado:
            st.success(resultado)
            st.balloons()
        else:
            st.error(resultado)

elif aba == "Consultar Banco":
    st.subheader("🔍 Histórico")
    dados = database.listar_etiquetas()
    if dados:
        df = pd.DataFrame(dados, columns=["QR Code", "SKU", "Pedido", "Data", "Status"])
        st.dataframe(df, use_container_width=True)