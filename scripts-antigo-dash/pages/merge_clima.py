import streamlit as st
from utils.assets import load_images


def map_card(title, badge, cls, img_base64):

    if img_base64:
        img_html = f'<img src="data:image/png;base64,{img_base64}" />'
    else:
        img_html = """
        <span style="color:#9CA3AF;font-size:12px">
            Sem imagem
        </span>
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

    # =========================
    # FILTROS
    # =========================

    c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1.5])

    with c1:
        st.markdown(
            '<div class="filter-label">PRODUTO</div>',
            unsafe_allow_html=True
        )

        produto = st.radio(
            "",
            ["Mapas Individuais", "Comparativos"],
            horizontal=True
        )

    with c2:
        st.markdown(
            '<div class="filter-label">ANO</div>',
            unsafe_allow_html=True
        )

        ano = st.selectbox(
            "",
            ["2025", "2024", "2023", "2022"]
        )

    with c3:
        st.markdown(
            '<div class="filter-label">MÊS</div>',
            unsafe_allow_html=True
        )

        mes = st.selectbox(
            "",
            [
                "Janeiro",
                "Fevereiro",
                "Março",
                "Abril",
                "Maio",
                "Junho",
                "Julho",
                "Agosto",
                "Setembro",
                "Outubro",
                "Novembro",
                "Dezembro"
            ]
        )

    with c4:
        st.markdown(
            '<div class="filter-label">ESCALA TEMPORAL</div>',
            unsafe_allow_html=True
        )

        escala = st.radio(
            "",
            ["Decêndio", "Quinzena", "Mês"],
            horizontal=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================
    # MAPAS
    # =========================

    mes_map = {
        "Janeiro": "01",
        "Fevereiro": "02",
        "Março": "03",
        "Abril": "04",
        "Maio": "05",
        "Junho": "06",
        "Julho": "07",
        "Agosto": "08",
        "Setembro": "09",
        "Outubro": "10",
        "Novembro": "11",
        "Dezembro": "12"
    }

    mes_num = mes_map[mes]

    escala_map = {

        "Decêndio": {
            "acum": f"acumulado_{ano}_{mes_num}_amazonia",
            "cat": f"categorico_{ano}_{mes_num}_amazonia",
            "filtro": "decendio",
            "label": "DECÊNDIO"
        },

        "Quinzena": {
            "acum": f"acumulado_{ano}_{mes_num}_amazonia",
            "cat": f"categorico_{ano}_{mes_num}_amazonia",
            "filtro": "quinzena",
            "label": "QUINZENA"
        },

        "Mês": {
            "acum": f"acumulado_{ano}_{mes_num}_amazonia",
            "cat": f"categorico_{ano}_{mes_num}_amazonia",
            "filtro": "mensal",
            "label": "MÊS"
        }
    }

    config = escala_map[escala]

    imgs_acum = load_images(
        config["acum"],
        config["filtro"]
    )

    imgs_cat = load_images(
        config["cat"],
        config["filtro"]
    )

    total = min(len(imgs_acum), len(imgs_cat))

    if total == 0:
        st.warning("Nenhuma imagem encontrada.")
        return

    # =========================
    # GRID
    # =========================

    for i in range(total):

        c1, c2 = st.columns(2)

        img_acum = imgs_acum[i]
        img_cat = imgs_cat[i]

        periodo = (
            f"{i+1}º {config['label']}"
            if total > 1
            else config["label"]
        )

        with c1:
            map_card(
                (
                    f"ACUMULADO — {i+1}º PERÍODO"
                    if total > 1
                    else "ACUMULADO — MENSAL"
                ),
                periodo,
                "verde",
                img_acum
            )

        with c2:
            map_card(
                (
                    f"CATEGÓRICO — {i+1}º PERÍODO"
                    if total > 1
                    else "CATEGÓRICO — MENSAL"
                ),
                periodo,
                "ciano",
                img_cat
            )