import streamlit as st
from utils.assets import load_images


def map_card(title, badge, cls, img_base64):
    if img_base64:
        img_html = f'<img src="data:image/png;base64,{img_base64}" />'
    else:
        img_html = """
        <div style="color:#9CA3AF; font-size:12px; height:200px; display:flex; align-items:center; justify-content:center; border:1px dashed #DDD; border-radius:4px;">
            Sem imagem cadastrada para este período
        </div>
        """

    st.markdown(
        f"""
        <div class="map-card">
            <div class="map-card-header">
                <span>{title}</span>
                <span class="badge {cls}">{badge}</span>
            </div>
            <div class="map-card-body">
                {img_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def get_image_for_period(ano, mes_num, escala, sub_periodo, tipo_prefixo):
    """
    Função auxiliar para buscar uma única imagem base64 com base nos filtros (usada no Comparativos).
    """
    filtro_map = {
        "Decêndio": "decendio",
        "Quinzena": "quinzena",
        "Mês": "mensal"
    }
    
    prefix = f"{tipo_prefixo}_{ano}_{mes_num}_amazonia"
    filtro = filtro_map[escala]
    
    lista_imgs = load_images(prefix, filtro)
    
    if escala in ["Decêndio", "Quinzena"] and sub_periodo:
        idx = int(sub_periodo) - 1
        if 0 <= idx < len(lista_imgs):
            return lista_imgs[idx]
        return None
    
    return lista_imgs[0] if lista_imgs else None


def render():
    # =========================
    # TÍTULO
    # =========================
    st.markdown("""
    <div class="main-title">
        Merge · Climatologia de Precipitação
    </div>
    <div class="subtitle">
        Análise categórica por decêndio · quinzena · mês — Amazônia Legal
    </div>
    """, unsafe_allow_html=True)

    meses_lista = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    
    mes_map = {m: f"{i+1:02d}" for i, m in enumerate(meses_lista)}

    # =========================
    # FILTROS GLOBAIS
    # =========================
    c1, c2 = st.columns([2, 3])

    with c1:
        st.markdown('<div class="filter-label">PRODUTO</div>', unsafe_allow_html=True)
        produto = st.radio("", ["Mapas Individuais", "Comparativos"], horizontal=True)

    with c2:
        st.markdown('<div class="filter-label">ESCALA TEMPORAL</div>', unsafe_allow_html=True)
        escala = st.radio("", ["Decêndio", "Quinzena", "Mês"], horizontal=True)

    st.markdown("---")

    # =========================
    # LÓGICA DE FILTROS DINÂMICOS
    # =========================
    if produto == "Mapas Individuais":
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="filter-label">ANO</div>', unsafe_allow_html=True)
            ano = st.selectbox("", ["2025", "2024", "2023", "2022"], key="ano_ind")
            
        with col2:
            st.markdown('<div class="filter-label">MÊS</div>', unsafe_allow_html=True)
            mes = st.selectbox("", meses_lista, key="mes_ind")

        # Configurações de busca para trazer a LISTA de todas as imagens do mês
        mes_num = mes_map[mes]
        filtro_escala = "decendio" if escala == "Decêndio" else "quinzena" if escala == "Quinzena" else "mensal"
        lbl_escala = "DECÊNDIO" if escala == "Decêndio" else "QUINZENA" if escala == "Quinzena" else "MÊS"

        imgs_acum = load_images(f"acumulado_{ano}_{mes_num}_amazonia", filtro_escala)
        imgs_cat = load_images(f"categorico_{ano}_{mes_num}_amazonia", filtro_escala)

        total = min(len(imgs_acum), len(imgs_cat))

        st.markdown("<br>", unsafe_allow_html=True)
        if total == 0:
            st.warning("Nenhuma imagem encontrada para os filtros selecionados.")
            return

        # Renderização em formato de Lista de todos os períodos encontrados do mês
        for i in range(total):
            grid_c1, grid_c2 = st.columns(2)
            
            periodo_label = f"{i+1}º {lbl_escala}" if total > 1 else lbl_escala
            titulo_acum = f"<b>ACUMULADO — {i+1}º PERÍODO</b>" if total > 1 else "<b>ACUMULADO — MENSAL</b>"
            titulo_cat = f"<b>CATEGÓRICO — {i+1}º PERÍODO</b>" if total > 1 else "<b>CATEGÓRICO — MENSAL</b>    "

            with grid_c1:
                map_card(titulo_acum, periodo_label, "verde", imgs_acum[i])
            with grid_c2:
                map_card(titulo_cat, periodo_label, "ciano", imgs_cat[i])
            st.markdown("<br>", unsafe_allow_html=True)

    else:
        # ==========================================
        # MODO COMPARATIVOS (4 IMAGENS CONTROLADAS)
        # ==========================================
        col_ini, col_fim = st.columns(2)

        with col_ini:
            st.markdown("### 🗓️ Período de Início")
            c_ano_i, c_mes_i, c_sub_i = st.columns(3)
            with c_ano_i:
                st.markdown('<div class="filter-label">ANO INÍCIO</div>', unsafe_allow_html=True)
                ano_i = st.selectbox("", ["2025", "2024", "2023", "2022"], key="ano_i")
            with c_mes_i:
                st.markdown('<div class="filter-label">MÊS INÍCIO</div>', unsafe_allow_html=True)
                mes_i = st.selectbox("", meses_lista, key="mes_i")
            with c_sub_i:
                sub_i = None
                if escala == "Decêndio":
                    st.markdown('<div class="filter-label">DECÊNDIO INÍCIO</div>', unsafe_allow_html=True)
                    sub_i = st.selectbox("", [1, 2, 3], key="dec_i")
                elif escala == "Quinzena":
                    st.markdown('<div class="filter-label">QUINZENA INÍCIO</div>', unsafe_allow_html=True)
                    sub_i = st.selectbox("", [1, 2], key="quin_i")

        with col_fim:
            st.markdown("### 🗓️ Período de Fim")
            c_ano_f, c_mes_f, c_sub_f = st.columns(3)
            with c_ano_f:
                st.markdown('<div class="filter-label">ANO FIM</div>', unsafe_allow_html=True)
                ano_f = st.selectbox("", ["2025", "2024", "2023", "2022"], index=1, key="ano_f")
            with c_mes_f:
                st.markdown('<div class="filter-label">MÊS FIM</div>', unsafe_allow_html=True)
                mes_f = st.selectbox("", meses_lista, key="mes_f")
            with c_sub_f:
                sub_f = None
                if escala == "Decêndio":
                    st.markdown('<div class="filter-label">DECÊNDIO FIM</div>', unsafe_allow_html=True)
                    sub_f = st.selectbox("", [1, 2, 3], key="dec_f")
                elif escala == "Quinzena":
                    st.markdown('<div class="filter-label">QUINZENA FIM</div>', unsafe_allow_html=True)
                    sub_f = st.selectbox("", [1, 2], key="quin_f")

        # Busca pontual das 4 imagens individuais do comparativo
        img_acum_i = get_image_for_period(ano_i, mes_map[mes_i], escala, sub_i, "acumulado")
        img_cat_i  = get_image_for_period(ano_i, mes_map[mes_i], escala, sub_i, "categorico")
        
        img_acum_f = get_image_for_period(ano_f, mes_map[mes_f], escala, sub_f, "acumulado")
        img_cat_f  = get_image_for_period(ano_f, mes_map[mes_f], escala, sub_f, "categorico")

        #st.markdown("<br>", unsafe_allow_html=True)

        badge_i = f"{sub_i}º {escala.upper()}" if sub_i else escala.upper()
        badge_f = f"{sub_f}º {escala.upper()}" if sub_f else escala.upper()

        # --- Linha 1: Período Inicial ---
        #st.markdown(f"#### 📊 Período Inicial: {mes_i.upper()} / {ano_i}")
        g1_c1, g1_c2 = st.columns(2)
        with g1_c1:
            map_card(f"ACUMULADO — {mes_i.upper()}/{ano_i}", badge_i, "verde", img_acum_i)
        with g1_c2:
            map_card(f"CATEGÓRICO — {mes_i.upper()}/{ano_i}", badge_i, "ciano", img_cat_i)

        #st.markdown("<br>", unsafe_allow_html=True)

        # --- Linha 2: Período Final ---
        #st.markdown(f"#### 📊 Período Final: {mes_f.upper()} / {ano_f}")
        g2_c1, g2_c2 = st.columns(2)
        with g2_c1:
            map_card(f"ACUMULADO — {mes_f.upper()}/{ano_f}", badge_f, "verde", img_acum_f)
        with g2_c2:
            map_card(f"CATEGÓRICO — {mes_f.upper()}/{ano_f}", badge_f, "ciano", img_cat_f)