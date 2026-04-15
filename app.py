import streamlit as st
import database
import logic
import pandas as pd

database.criar_tabelas()

st.set_page_config(page_title="Logística Paulo", page_icon="📦")
# Removi o layout="wide" para os campos ficarem centralizados e menores
st.title("📦 Sistema de Etiquetas QRCODE")

# No início do app.py, logo abaixo do st.title
col_logo1, col_logo2 = st.columns([1, 4])
with col_logo1:
    # Substitua 'logo.png' pelo nome do seu arquivo de imagem
    try:
        st.image("logo.png", width=100)
    except:
        st.write("🏢") # Caso não ache a imagem, mostra um ícone
with col_logo2:
    st.write("### Logcare Logística")
    st.write("Departamento de Logística e Expedição")

aba = st.sidebar.radio("Navegação:", ["Gerar Etiquetas", "Expedição", "Consultar Banco"])

if aba == "Gerar Etiquetas":
    st.subheader("🛠️ Emissão de Lote")
    sku_selecionado = st.selectbox("Selecione o SKU", list(logic.PRODUTOS.keys()))
    descricao = logic.PRODUTOS[sku_selecionado]
    
    col1, col2 = st.columns(2)
    with col1:
        pedido = st.text_input("Número do Pedido")
    with col2:
        qtd = st.number_input("Quantidade", min_value=1, value=1, step=1)

    if st.button("Gerar Lote de Etiquetas"):
        if not pedido:
            st.warning("Informe o número do pedido!")
        else:
            prefixo = logic.extrair_prefixo(sku_selecionado)
            ultimo_valor = database.buscar_ultimo_num(prefixo)
            
            dados_lote = []
            for i in range(1, int(qtd) + 1):
                novo_codigo = f"{prefixo}{str(ultimo_valor + i).zfill(10)}"
                database.salvar_etiqueta(novo_codigo, sku_selecionado, pedido)
                dados_lote.append((novo_codigo, sku_selecionado, descricao))
            
            pdf_bytes = logic.gerar_pdf_lote(dados_lote)
            st.success(f"✅ {len(dados_lote)} etiquetas salvas no banco!")
            
            st.download_button(
                label="📥 Baixar Etiquetas (PDF)",
                data=pdf_bytes,
                file_name=f"lote_pedido_{pedido}.pdf",
                mime="application/pdf"
            )

elif aba == "Expedição":
    st.subheader("🚚 Módulo de Expedição")
    codigo_lido = st.text_input("Bipe o QR Code aqui", key="scan")
    if codigo_lido:
        resultado = database.atualizar_status_expedicao(codigo_lido)
        if "✅" in resultado:
            st.success(resultado)
        else:
            st.warning(resultado)

elif aba == "Consultar Banco":
    st.subheader("🔍 Histórico e Relatórios")
    dados = database.listar_etiquetas()
    
    if dados:
        df = pd.DataFrame(dados, columns=["QR Code", "SKU", "Pedido", "Data Criação", "Status"])
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        st.subheader("📋 Gerar Checklist de Pedido Antigo")
        
        pedidos_unicos = sorted(df['Pedido'].unique())
        pedido_para_relatorio = st.selectbox("Escolha o pedido", pedidos_unicos)
        
        if st.button("Preparar Relatório"):
            itens_pedido = database.buscar_etiquetas_por_pedido(pedido_para_relatorio)
            dados_completos = []
            for item in itens_pedido:
                cod, sku, status = item
                desc = logic.PRODUTOS.get(sku, "Descrição não encontrada")
                dados_completos.append((cod, sku, desc))
            
            pdf_relatorio = logic.gerar_relatorio_conferencia(pedido_para_relatorio, dados_completos)
            
            st.download_button(
                label=f"📥 Baixar Checklist Pedido {pedido_para_relatorio}",
                data=pdf_relatorio,
                file_name=f"checklist_pedido_{pedido_para_relatorio}.pdf",
                mime="application/pdf"
            )