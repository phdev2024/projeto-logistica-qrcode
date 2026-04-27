import streamlit as st
import database
import logic
import pandas as pd
import importlib
from datetime import datetime

# 1. INICIALIZAÇÃO DO BANCO E DO ESTADO
database.criar_tabelas()

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

st.set_page_config(page_title="Logcare Logística", page_icon="📦")

# 2. SISTEMA DE LOGIN
if not st.session_state.autenticado:
    st.subheader("🔐 Acesso Restrito - Logcare")
    user_in = st.text_input("Usuário")
    pass_in = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        usuarios_permitidos = {
            "Paulo": "log123",
            "admin": "admin",
            "Flavia": "logflavia",
            "Vanessa": "logvanessa",
            "Vinicius": "logvinicius"
        }
        
        if user_in in usuarios_permitidos and usuarios_permitidos[user_in] == pass_in:
            st.session_state.autenticado = True
            st.session_state.usuario_logado = user_in
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos")
    st.stop()

# 3. CONFIGURAÇÃO DO MENU
ADMIN_USER = "Paulo"
opcoes_menu = ["Gerar Etiquetas", "Expedição", "Consultar Banco"]

if st.session_state.usuario_logado == ADMIN_USER:
    opcoes_menu.append("Gestão de Usuários")

aba = st.sidebar.radio("Navegação:", opcoes_menu)

st.sidebar.divider()
if st.sidebar.button("🔄 Atualizar Lista de Produtos"):
    importlib.reload(logic)
    st.rerun()

if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

st.title("📦 Sistema de Etiquetas QRCODE")

col_l1, col_l2 = st.columns([1, 4])
with col_l1:
    try: st.image("logo.png", width=100)
    except: st.write("🏢")
with col_l2:
    st.write("### Logcare Logística")
    st.write("Departamento de Logística e Expedição")

# --- CONTEÚDO DAS ABAS ---

if aba == "Gerar Etiquetas":
    st.subheader("🛠️ Emissão de Lote")
    col_sel, col_v1 = st.columns([2, 1])
    with col_sel:
        sku_sel = st.selectbox("Selecione o SKU", list(logic.PRODUTOS.keys()))
        descricao = logic.PRODUTOS[sku_sel]
        st.info(f"Produto: {descricao}")

    col1, col2 = st.columns([2, 1])
    with col1:
        pedido = st.text_input("Número do Pedido")
    with col2:
        qtd = st.number_input("Quantidade", min_value=1, value=1)

    if st.button("Gerar Lote de Etiquetas"):
        if not pedido:
            st.warning("Informe o pedido!")
        else:
            with st.spinner("Processando lote e salvando no Google Sheets..."):
                prefixo = logic.extrair_prefixo(sku_sel)
                ultimo = database.buscar_ultimo_num(prefixo)
                
                dados_para_planilha = [] # Lista para o Google Sheets
                dados_para_pdf = []      # Lista para o PDF
                
                data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                # Prepara o lote todo na memória primeiro
                for i in range(1, int(qtd) + 1):
                    novo_cod = f"{prefixo}{str(ultimo + i).zfill(10)}"
                    
                    # Formato da linha: QR Code, SKU, Pedido, Data, Status, Criado Por, Expedido Por
                    linha = [novo_cod, sku_sel, pedido, data_atual, "Pendente", st.session_state.usuario_logado, ""]
                    dados_para_planilha.append(linha)
                    
                    dados_para_pdf.append((novo_cod, sku_sel, descricao))
                
                # ENVIO ÚNICO PARA O BANCO (Batch Update) - Resolve o erro 429
                sucesso = database.salvar_lote_etiquetas(dados_para_planilha)
                
                if sucesso:
                    pdf_bytes = logic.gerar_pdf_lote(dados_para_pdf)
                    st.success(f"✅ Lote de {qtd} etiquetas salvo e gerado com sucesso!")
                    st.download_button("📥 Baixar Etiquetas (PDF)", pdf_bytes, f"pedido_{pedido}.pdf", "application/pdf")
                else:
                    st.error("Erro ao salvar no banco de dados. Tente novamente.")

elif aba == "Expedição":
    st.subheader("🚚 Módulo de Expedição")
    cod_lido = st.text_input("Bipe o QR Code aqui")
    if cod_lido:
        res = database.atualizar_status_expedicao(cod_lido, st.session_state.usuario_logado)
        st.info(res)

elif aba == "Consultar Banco":
    st.subheader("🔍 Histórico e Relatórios")
    dados = database.listar_etiquetas()
    if dados:
        df = pd.DataFrame(dados, columns=["QR Code", "SKU", "Pedido", "Data", "Status", "Criado Por", "Expedido Por"])
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        st.subheader("📋 Checklist de Conferência")
        pedidos_disp = sorted(df['Pedido'].unique())
        ped_sel = st.selectbox("Escolha o Pedido:", pedidos_disp)
        
        if st.button("Gerar PDF de Checklist"):
            itens_ped = database.buscar_etiquetas_por_pedido(ped_sel)
            if itens_ped:
                dados_conf = []
                for it in itens_ped:
                    c, s, stt = it
                    d = logic.PRODUTOS.get(s, "Descrição não encontrada")
                    dados_conf.append((c, s, d))
                pdf_check = logic.gerar_relatorio_conferencia(ped_sel, dados_conf)
                st.download_button(f"📥 Baixar Checklist {ped_sel}", pdf_check, f"check_{ped_sel}.pdf", "application/pdf")

# --- BLOCO DE REIMPRESSÃO (LOTE OU INDIVIDUAL) ---
        st.divider()
        st.subheader("🖨️ Reimpressão de Etiquetas")
        
        aba_reimprimir = st.tabs(["Por Pedido (Lote)", "Por Código Único (Individual)"])
        
        with aba_reimprimir[0]:
            ped_reimprimir = st.selectbox("Selecione o Pedido:", pedidos_disp, key="re_ped")
            if st.button("Gerar PDF do Pedido"):
                itens = database.buscar_etiquetas_por_pedido(ped_reimprimir)
                if itens:
                    dados = [(it[0], it[1], logic.PRODUTOS.get(it[1], "N/A")) for it in itens]
                    pdf = logic.gerar_pdf_lote(dados)
                    st.download_button(f"📥 Baixar Lote {ped_reimprimir}", pdf, f"lote_{ped_reimprimir}.pdf")

        with aba_reimprimir[1]:
            cod_individual = st.text_input("Digite o Código do QR Code (ex: LOG0000000001)")
            if st.button("Gerar Etiqueta Individual"):
                if cod_individual:
                    # Busca os dados dessa etiqueta específica no DataFrame que já carregamos na tela
                    # d[0] é o QR Code, d[1] é o SKU
                    match = [d for d in dados if d[0] == cod_individual]
                    
                    if match:
                        q, s, p, dt, stt, u1, u2 = match[0]
                        desc = logic.PRODUTOS.get(s, "Produto não encontrado")
                        # Geramos o PDF com apenas um item na lista
                        pdf_uni = logic.gerar_pdf_lote([(q, s, desc)])
                        st.success(f"✅ Etiqueta {q} localizada!")
                        st.download_button(f"📥 Baixar Etiqueta {q}", pdf_uni, f"etiqueta_{q}.pdf")
                    else:
                        st.error("Código não encontrado no banco de dados.")
                else:
                    st.warning("Digite um código válido.")

elif aba == "Gestão de Usuários":
    st.subheader("👥 Gestão de Acessos (Admin)")
    st.success(f"Você está logado como ADMINISTRADOR: {st.session_state.usuario_logado}")
    
    usuarios_credenciais = {
        "Paulo": "log123", "admin": "admin", "Flavia": "logflavia", 
        "Vanessa": "logvanessa", "Vinicius": "logvinicius"
    }
    df_usuarios = pd.DataFrame(list(usuarios_credenciais.items()), columns=["Usuário", "Senha"])
    st.table(df_usuarios)