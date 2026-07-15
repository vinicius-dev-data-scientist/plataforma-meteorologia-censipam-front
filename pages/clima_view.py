import streamlit as st
import os
import glob
import base64
from datetime import datetime

# =====================================================
# PATHS
# =====================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# Se sua pasta 'img' estiver dentro de 'static', mude para:
# PATH_IMGS = os.path.join(BASE_DIR, "static", "img", "Figuras")
PATH_IMGS = os.path.join(
    BASE_DIR,
    "img",
    "Figuras"
)


# =====================================================
# AUXILIAR: CARREGAMENTO BASE64
# =====================================================

def converter_para_base64(path):
    with open(path, "rb") as f:
        return (
            "data:image/png;base64,"
            + base64.b64encode(f.read()).decode()
        )


# =====================================================
# CARREGAMENTO E CLASSIFICAÇÃO DAS IMAGENS
# =====================================================

@st.cache_data(show_spinner="📂 Carregando produtos climáticos...")
def carregar_clima_separado(ano, mes, dia):
    pasta = os.path.join(
        PATH_IMGS,
        "Clima",
        ano,
        mes,
        dia
    )

    grupos = {
        "SST": [],
        "Vento": [],
        "Clima + Merge": []
    }

    if not os.path.exists(pasta):
        return grupos
    
    arquivos = sorted(
        glob.glob(
            os.path.join(
                pasta,
                "*.png"
            )
        )
    )

    for arq in arquivos:
        nome_arq = os.path.basename(arq).lower()
        b64_img = converter_para_base64(arq)
        
        # Gera o título amigável baseado no nome do arquivo
        titulo = os.path.splitext(os.path.basename(arq))[0].replace("_", " ").upper()

        item = {
            "titulo": titulo,
            "img": b64_img,
            "nome_original": nome_arq
        }

        # Regras de Classificação:
        # 1. Vento: Qualquer imagem que contenha "vento" no nome
        if "vento" in nome_arq:
            grupos["Vento"].append(item)
            
        # 2. Clima + Merge: Qualquer imagem que contenha "hadley", "walker" ou "merge_anomalia"
        elif any(x in nome_arq for x in ["hadley", "walker", "merge_anomalia"]):
            grupos["Clima + Merge"].append(item)
            
        # 3. SST: Restante das imagens
        else:
            grupos["SST"].append(item)

    return grupos


# =====================================================
# COMPONENTE VISUAL PADRONIZADO (CARD)
# =====================================================

def render_map_card(titulo, img_base64, max_height=480):
    """
    Gera o card de visualização padronizando o tamanho das imagens
    e garantindo responsividade perfeita para os mapas climáticos.
    """
    st.markdown(
        f"""
        <div class="map-card" style="margin-bottom: 20px;">
            <div class="map-card-header">
                <span>{titulo}</span>
            </div>
            <div class="map-card-body" style="display: flex; justify-content: center; align-items: center; background: #F9FAFB; padding: 10px; border-radius: 0 0 8px 8px;">
                <img src="{img_base64}" style="max-width: 100%; height: auto; max-height: {max_height}px; object-fit: contain; border-radius: 4px;" />
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =====================================================
# RENDER PRINCIPAL
# =====================================================

def render():

    st.markdown(
        """
        <div class="main-title">
            Análise Climatológica
        </div>
        <div class="subtitle">
            Anomalias de SST, Linhas de Corrente e Circulações Globais
        </div>
        """,
        unsafe_allow_html=True
    )

    # Filtro de Data Superior
    with st.container(border=True):
        c1, _ = st.columns([0.3, 0.7])
        with c1:
            data = st.date_input(
                "DATA DE REFERÊNCIA",
                value=datetime.today(),
                format="DD/MM/YYYY"
            )

    # Extração das strings correspondentes aos diretórios
    ano_str = str(data.year)
    mes_str = f"{data.month:02d}"
    dia_str = f"{data.day:02d}"

    # Carrega dados do diretório correto
    grupos = carregar_clima_separado(ano_str, mes_str, dia_str)

    # Soma das imagens carregadas
    total_imagens = sum(len(lista) for lista in grupos.values())

    if total_imagens == 0:
        st.warning(
            f"⚠️ Nenhuma imagem de produto climática encontrada na pasta: Clima/{ano_str}/{mes_str}/{dia_str}"
        )
        return

    # Interface de Seleção usando st.radio Horizontal (Estilo Merge Clima)
    st.markdown("<br>", unsafe_allow_html=True)
    
    categoria_selecionada = st.radio(
        "",
        ["SST", "Vento", "Clima + Merge"],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Recupera a lista filtrada de imagens da aba selecionada
    imagens_exibicao = grupos[categoria_selecionada]

    if not imagens_exibicao:
        st.info(f"Nenhum produto de **{categoria_selecionada}** disponível para esta data.")
        return

    # =====================================================
    # LAYOUT PERSONALIZADO PARA SST
    # =====================================================
    if categoria_selecionada == "SST":
        # Separar índices dos mapas espaciais
        indices = []
        mapas_espaciais = []
        
        for item in imagens_exibicao:
            if "indice" in item["nome_original"]:
                indices.append(item)
            else:
                mapas_espaciais.append(item)

        # 1. Mostrar os Índices lado a lado (2 colunas)
        if indices:
            cols_ind = st.columns(2)
            for idx, item in enumerate(indices):
                col_atual = cols_ind[idx % 2]
                with col_atual:
                    render_map_card(item["titulo"], item["img"], max_height=420)

        # 2. Mostrar os mapas de SST empilhados (Largura total, um abaixo do outro)
        for item in mapas_espaciais:
            # Aumentamos o max_height para 650px para dar uma visão bem ampliada de cada mapa espacial
            render_map_card(item["titulo"], item["img"], max_height=650)

    # =====================================================
    # LAYOUT PADRÃO (OUTRAS ABAS)
    # =====================================================
    else:
        # Exibição organizada em duas colunas padronizadas
        cols = st.columns(2)
        for idx, item in enumerate(imagens_exibicao):
            col_atual = cols[idx % 2]
            with col_atual:
                render_map_card(item["titulo"], item["img"])


if __name__ == "__main__":
    render()