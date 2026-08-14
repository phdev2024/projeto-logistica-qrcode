import streamlit as st
import base64
import os

# Paleta Oficial Logcare
COR_PRIMARIA = "#008f84"
COR_SECUNDARIA = "#00bba9"
COR_ESCURA = "#306359"
COR_FUNDO_CARD = "#f8faf9"

def aplicar_estilos_customizados():
    """
    Aplica o design corporativo da Logcare em toda a interface do Streamlit.
    """
    css = f"""
    <style>
        /* Ajuste de espaçamento superior da página */
        .block-container {{
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
        }}

        /* 1. Botões de Ação Principal */
        .stButton>button {{
            background-color: {COR_PRIMARIA};
            color: white !important;
            border-radius: 8px;
            border: none;
            padding: 0.5rem 1.2rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }}
        .stButton>button:hover {{
            background-color: {COR_SECUNDARIA};
            color: white !important;
            box-shadow: 0 4px 10px rgba(0, 187, 169, 0.3);
            transform: translateY(-1px);
        }}

        /* 2. Cartões de Métricas (KPIs) */
        div[data-testid="stMetric"] {{
            background-color: {COR_FUNDO_CARD};
            border-left: 5px solid {COR_PRIMARIA};
            padding: 12px 18px;
            border-radius: 8px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        }}
        div[data-testid="stMetricLabel"] {{
            color: {COR_ESCURA};
            font-weight: 600;
            font-size: 0.95rem;
        }}
        div[data-testid="stMetricValue"] {{
            color: #1a1a1a;
            font-weight: 700;
        }}

        /* 3. Barra Lateral */
        section[data-testid="stSidebar"] {{
            background-color: #fbfdfc;
            border-right: 1px solid #e2e8e5;
        }}

        /* 4. Estilização do Header Executivo */
        .header-container {{
            background: linear-gradient(90deg, #306359 0%, #008f84 100%);
            padding: 12px 24px;
            border-radius: 4px !important;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0, 143, 132, 0.15);
        }}
        .header-title {{
            color: #ffffff !important;
            font-size: 1.7rem;
            font-weight: 800;
            margin: 0;
            line-height: 1.2;
        }}
        .header-subtitle {{
            color: #e0f2f1;
            font-size: 0.92rem;
            margin: 2px 0 0 0;
            font-weight: 400;
        }}
        .user-badge {{
            background-color: rgba(255, 255, 255, 0.18);
            border: 1px solid rgba(255, 255, 255, 0.35);
            color: #ffffff;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.88rem;
            font-weight: 600;
            backdrop-filter: blur(4px);
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def renderizar_cabecalho_executivo(usuario_logado):
    """
    Renderiza uma faixa verde executiva integrada com Logo, Título e Usuário.
    """
    # Converte o logo local em base64 para renderizar perfeitamente dentro do HTML
    logo_html = ""
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            logo_html = f'<img src="data:image/png;base64,{encoded_string}" style="height: 38px; margin-right: 15px; filter: brightness(0) invert(1);">'
    else:
        logo_html = '<span style="font-size: 1.8rem;">📦</span>'

    header_html = f"""
    <div class="header-container" style="padding: 12px 24px; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; justify-content: flex-start;">
            {logo_html}
            <div style="margin-left: 20px;">
                <h1 class="header-title" style="font-size: 1.35rem; font-weight: 700; color: #ffffff; margin: 0;">
                    Gestão de Expedição & Ocupação de Estoque
                </h1>
                </div>
        </div>
        <div>
            <span class="user-badge">👤 {usuario_logado}</span>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)