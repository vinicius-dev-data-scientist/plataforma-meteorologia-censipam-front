import base64
import os
import re
import time
from datetime import datetime
from pathlib import Path

import folium
import numpy as np
import streamlit as st
from folium.plugins import Fullscreen
from folium.raster_layers import ImageOverlay
from streamlit_folium import folium_static

# ======== CONFIGURAÇÕES ORIGINAIS =========
LONS = [-62.3126, -57.6701]
LATS = [-5.4564, -0.8221]
DATA_INICIAL = datetime(2025, 8, 28)

BASE_DIR = Path(__file__).resolve().parent.parent
PATH_IMGS = BASE_DIR / "static" / "img" / "FIGS_CAPPI" / "FIGS_CAPPI"
PADRAO = re.compile(r"(\d{8})_(\d{4})")


# ==========================================
# FUNÇÕES DE SUPORTE
# ==========================================
@st.cache_data(show_spinner="Carregando imagem...")
def carregar_imagem(caminho):
    with open(caminho, "rb") as f:
        return f.read()


def criar_mapa(img64):
    bounds = [[LATS[0], LONS[0]], [LATS[1], LONS[1]]]
    mapa = folium.Map(
        location=[np.mean(LATS), np.mean(LONS)],
        zoom_start=8,
    )
    mapa.fit_bounds(bounds)
    Fullscreen().add_to(mapa)

    ImageOverlay(
        image=img64,
        bounds=bounds,
        opacity=0.60,
        interactive=True,
    ).add_to(mapa)

    folium.Rectangle(
        bounds=bounds,
        color="red",
        fill=False,
    ).add_to(mapa)

    return mapa


# ==========================================
# RENDERIZAÇÃO DA PÁGINA
# ==========================================
def render():
    # 1. Validação de Diretório
    if not PATH_IMGS.exists():
        st.error(f"Pasta não encontrada:\n\n{PATH_IMGS}")
        return

    arquivos = sorted(PATH_IMGS.glob("*.png"))
    if not arquivos:
        st.warning("Nenhuma imagem encontrada na pasta FIGS_CAPPI.")
        return

    # 2. Agrupamento por Data
    imagens_por_data = {}
    for arq in arquivos:
        resultado = PADRAO.search(arq.name)
        if resultado is None:
            continue
        
        data_str = resultado.group(1)
        data_dt = datetime.strptime(data_str, "%Y%m%d")

        if data_dt < DATA_INICIAL:
            continue

        imagens_por_data.setdefault(data_str, []).append(arq)

    if not imagens_por_data:
        st.warning("Nenhuma data válida encontrada posterior à data limite.")
        return

    datas = sorted(imagens_por_data.keys(), reverse=True)

    # 3. Filtros Superiores (Estilo merge_clima.py)
    col_modo, col_data = st.columns([2, 3])

    with col_modo:
        st.markdown('<div class="filter-label">MODO DE OPERAÇÃO</div>', unsafe_allow_html=True)
        modo = st.radio(
            "", 
            ["Operacional", "Intervalo"], 
            horizontal=True, 
            key="radar_modo"
        )

    with col_data:
        st.markdown('<div class="filter-label">DATA DE OBSERVAÇÃO</div>', unsafe_allow_html=True)
        data_selecionada = st.selectbox(
            "",
            datas,
            format_func=lambda d: datetime.strptime(d, "%Y%m%d").strftime("%d/%m/%Y"),
            key="radar_data_sel"
        )

    st.markdown("---")

    # 4. Extração e mapeamento de horários do dia selecionado
    arquivos_dia = sorted(imagens_por_data[data_selecionada])
    horarios_formatados = []
    mapa_arquivos = {}

    for arq in arquivos_dia:
        resultado = PADRAO.search(arq.name)
        hora = resultado.group(2)
        horario_str = datetime.strptime(
            f"{data_selecionada}{hora}", "%Y%m%d%H%M"
        ).strftime("%d/%m/%Y %H:%M")
        
        horarios_formatados.append(horario_str)
        mapa_arquivos[horario_str] = arq

    # 5. Definição do escopo de horários com base no Modo selecionado
    if modo == "Operacional":
        horarios_opcao = horarios_formatados[-10:]
    else:
        st.markdown("### ⏱️ Definição do Intervalo de Tempo")
        col_ini, col_fim = st.columns(2)
        
        with col_ini:
            st.markdown('<div class="filter-label">HORÁRIO INÍCIO</div>', unsafe_allow_html=True)
            hora_inicio = st.selectbox("", horarios_formatados, index=0, key="rad_intervalo_ini")
            
        with col_fim:
            idx_ini_limite = horarios_formatados.index(hora_inicio)
            st.markdown('<div class="filter-label">HORÁRIO FIM</div>', unsafe_allow_html=True)
            hora_fim = st.selectbox(
                "", 
                horarios_formatados[idx_ini_limite:], 
                index=len(horarios_formatados[idx_ini_limite:]) - 1, 
                key="rad_intervalo_fim"
            )
            
        idx_fim_real = horarios_formatados.index(hora_fim)
        horarios_opcao = horarios_formatados[idx_ini_limite : idx_fim_real + 1]

    if not horarios_opcao:
        st.warning("Nenhum horário disponível para a seleção atual.")
        return

    # ==============================================================================
    # CONTROLE DE ESTADO SEGURO DO AUTO PLAY (Sem usar a key do Slider diretamente)
    # ==============================================================================
    
    # Índice numérico puro para controlar qual item da lista está ativo
    if "radar_active_index" not in st.session_state:
        st.session_state.radar_active_index = 0

    # Evita transbordamento do índice ao alternar datas ou modos
    if st.session_state.radar_active_index >= len(horarios_opcao):
        st.session_state.radar_active_index = 0

    # Cria duas colunas para o Autoplay e o Slider ficarem lado a lado
    col_play, col_slider = st.columns([1, 4])

    with col_play:
        st.write("")  # Pequeno ajuste vertical
        st.write("")
        # Checkbox com chave única
        autoplay = st.checkbox("🔄 Auto Play", value=False, key="radar_autoplay_chk")

    with col_slider:
        # Pega o horário correto baseado no nosso índice de estado
        valor_default = horarios_opcao[st.session_state.radar_active_index]
        
        # Slider sem usar parâmetro "key" para evitar o erro de mutabilidade bloqueada
        horario_selecionado = st.select_slider(
            "Horários Disponíveis:",
            options=horarios_opcao,
            value=valor_default
        )
        
        # Se o usuário arrastar o slider manualmente, atualizamos o nosso índice de estado
        st.session_state.radar_active_index = horarios_opcao.index(horario_selecionado)

    # ==========================================
    # CARD DE INFORMAÇÃO E RENDERIZAÇÃO DO MAPA
    # ==========================================

    # Carrega e exibe o mapa
    arquivo_alvo = mapa_arquivos[horario_selecionado]
    img_data = carregar_imagem(arquivo_alvo)
    img64 = base64.b64encode(img_data).decode("utf-8")
    data_url = f"data:image/png;base64,{img64}"

    mapa = criar_mapa(data_url)
    folium_static(mapa, width=1400, height=800)

    # ==========================================
    # PROCESSAMENTO DO PRÓXIMO PASSO (FIM DO ARQUIVO)
    # ==========================================
    if autoplay and len(horarios_opcao) > 1:
        # Tempo de transição suave
        time.sleep(1.0)
        
        # Incrementa o índice de forma circular
        st.session_state.radar_active_index = (st.session_state.radar_active_index + 1) % len(horarios_opcao)
        
        # Executa o rerun de forma limpa
        st.rerun()


if __name__ == "__main__":
    render()