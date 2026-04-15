import streamlit as st
import database
import logic
import pandas as pd

database.criar_tabelas()

st.set_page_config(page_title="Logcare Logística", page_icon="📦")

# --- SISTEMA DE LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.subheader("🔐 Acesso Restrito - Logcare Logística")
    user_input = st.text_input("Usuário")
    pass_input = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if (user_input == "paulo" and pass_input == "log123") or (user_input == "admin" and pass_input == "admin"):
            st.session_state.autenticado = True
            st.session_state.usuario_logado = "Paulo Henrique"
            st.rerun()

        elif(user_input == "flavia" and pass_input == "logflavia"):
            st.session_state.autenticado = True
            st.session_state.usuario_logado = "Flavia"
            st.rerun()
            st.error("Usuário ou senha incorretos")

        elif(user_input == "vanessa" and pass_input == "logvanessa"):
            st.session_state.autenticado = True
            st.session_state.usuario_logado = "Vanessa"
            st.rerun()

        elif(user_input == "vinicius" and pass_input == "logvinicius"):
            st.session_state.autenticado = True
            st.session_state.usuario_logado = "Vinicius"
            st.rerun()
            
        else:
            st.error("Usuário ou senha incorretos")
    st.stop()
# --- INTERFACE DO APP (SÓ ACESSA SE LOGADO) ---
st.sidebar.write(f"👤 Operador: **{st.session_state.usuario_logado}**")
if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

st.title("📦 Sistema de Etiquetas QRCODE")

# Cabeçalho com Logo
col_logo1, col_logo2 = st.columns([1, 4])
with col_logo1:
    try:
        st.image("logo.png", width=100)
    except:
        st.write("🏢")
with col_logo2:
    st.write("### Logcare Logística")
    st.write("Departamento de Logística e Expedição")

aba = st.sidebar.radio("Navegação:", ["Gerar Etiquetas", "Expedição", "Consultar Banco"])

if aba == "Gerar Etiquetas":
    st.subheader("🛠️ Emissão de Lote")
    
    # Criamos 3 colunas, mas usamos apenas a primeira para o SKU
    # [2, 1, 1] significa que a primeira coluna é o dobro das outras
    col_sku, col_vazia1, col_vazia2 = st.columns([2, 1, 1])
    
    with col_sku:
        sku_selecionado = st.selectbox("Selecione o SKU", list(logic.PRODUTOS.keys()))
        descricao = logic.PRODUTOS[sku_selecionado]
    
    # Linha debaixo: Pedido e Quantidade
    col1, col2, col3 = st.columns([2, 1, 1])
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
                # PASSANDO USUÁRIO PARA O BANCO
                database.salvar_etiqueta(novo_codigo, sku_selecionado, pedido, st.session_state.usuario_logado)
                dados_lote.append((novo_codigo, sku_selecionado, descricao))
            
            pdf_bytes = logic.gerar_pdf_lote(dados_lote)
            st.success(f"✅ {len(dados_lote)} etiquetas geradas por {st.session_state.usuario_logado}!")
            
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
        # PASSANDO USUÁRIO PARA A EXPEDIÇÃO
        resultado = database.atualizar_status_expedicao(codigo_lido, st.session_state.usuario_logado)
        if "✅" in resultado:
            st.success(resultado)
        else:
            st.warning(resultado)

elif aba == "Consultar Banco":
    st.subheader("🔍 Histórico e Relatórios")
    dados = database.listar_etiquetas()
    
    if dados:
        df = pd.DataFrame(dados, columns=["QR Code", "SKU", "Pedido", "Data Criação", "Status", "Criado Por", "Expedido Por"])
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        st.subheader("📋 Gerar Checklist Retroativo")
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