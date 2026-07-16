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

def render_map_card(titulo, img_base64, max_height=None):
    """
    Gera o card de visualização mantendo a proporção real da imagem.
    Adiciona margens de segurança (max-width: 95%) para evitar cortes nas bordas.
    """
    style_img = "max-width: 95%; height: auto; display: block; margin: 0 auto; border-radius: 4px;"
    if max_height:
        style_img += f" max-height: {max_height}px; object-fit: contain;"

    st.markdown(
        f"""
        <div class="map-card" style="margin-bottom: 20px;">
            <div class="map-card-header">
                <span>{titulo}</span>
            </div>
            <div class="map-card-body" style="display: flex; justify-content: center; align-items: center; background: #F9FAFB; padding: 15px; border-radius: 0 0 8px 8px;">
                <img src="{img_base64}" style="{style_img}" />
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

    # Interface de Seleção usando st.radio Horizontal
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
        # Separar listas para organizar na tela de acordo com os filtros de nomes
        indices = []
        evolucoes_atlantico = []
        evolucoes_pacifico = []
        mapas_espaciais = []
        
        for item in imagens_exibicao:
            nome_norm = item["nome_original"]
            if "indice" in nome_norm:
                indices.append(item)
            elif "evolucao" in nome_norm and "atlantico" in nome_norm:
                evolucoes_atlantico.append(item)
            elif "evolucao" in nome_norm and "pacifico" in nome_norm:
                evolucoes_pacifico.append(item)
            else:
                mapas_espaciais.append(item)

        # 1º: ÍNDICES SST (Lado a Lado - 2 Colunas)
        if indices:
            cols_ind = st.columns(2)
            for idx, item in enumerate(indices):
                col_atual = cols_ind[idx % 2]
                with col_atual:
                    render_map_card(item["titulo"], item["img"], max_height=None)

        # 2º: EVOLUÇÃO ATLÂNTICO (Lado a Lado - 2 Colunas - Logo abaixo dos índices)
        if evolucoes_atlantico:
            cols_evo_atl = st.columns(2)
            for idx, item in enumerate(evolucoes_atlantico):
                col_atual = cols_evo_atl[idx % 2]
                with col_atual:
                    render_map_card(item["titulo"], item["img"], max_height=None)

        # 3º: EVOLUÇÃO PACÍFICO (Um embaixo do outro - Largura Total)
        if evolucoes_pacifico:
            for item in evolucoes_pacifico:
                render_map_card(item["titulo"], item["img"], max_height=500)

        # 4º: MAPAS ESPACIAIS DE SST (Um embaixo do outro - No final da página)
        for item in mapas_espaciais:
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