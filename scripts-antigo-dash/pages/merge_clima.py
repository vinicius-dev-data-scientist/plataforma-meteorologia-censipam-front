import os
import base64
import streamlit as st
import streamlit.components.v1 as components

def render():

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    img_dir = os.path.join(BASE_DIR, "..", "img", "OLDS")

    def load_img_base64(path):
        with open(path, "rb") as img:
            return base64.b64encode(img.read()).decode()

    def load_images(folder, prefix, filtro):
        images = []
        for f in os.listdir(folder):
            if prefix in f and filtro in f:
                full_path = os.path.join(folder, f)
                images.append(load_img_base64(full_path))
        return sorted(images)

# =========================
# SATÉLITE - MERGE CLIMATOLOGIA
# =========================

# =========================
# TÍTULO
# =========================
st.markdown("""
<div class="main-title">Merge · Climatologia de Precipitação</div>
<div class="subtitle">
Análise categórica por decêndio · quinzena · mês — Amazônia Legal
</div>
""", unsafe_allow_html=True)

# =========================
# FILTROS
# =========================
c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1.5])

with c1:
    st.markdown('<div class="filter-label">PRODUTO</div>', unsafe_allow_html=True)
    produto = st.radio("", ["Mapas Individuais", "Comparativos"], horizontal=True)

with c2:
    st.markdown('<div class="filter-label">ANO</div>', unsafe_allow_html=True)
    ano = st.selectbox("", ["2025","2024", "2023", "2022"])

with c3:
    st.markdown('<div class="filter-label">MÊS</div>', unsafe_allow_html=True)
    mes = st.selectbox("", ["Janeiro","Fevereiro","Março","Abril", "Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"])

with c4:
    st.markdown('<div class="filter-label">ESCALA TEMPORAL</div>', unsafe_allow_html=True)
    escala = st.radio("", ["Decêndio","Quinzena","Mês"], horizontal=True)

st.markdown("<br>", unsafe_allow_html=True)

mes_map = {
    "Janeiro": "01",
    "Fevereiro": "02",
    "Março": "03",
    "Abril": "04"
}

mes_num = mes_map[mes]

escala_map = {
    "Decêndio": {
        "acum": f"acumulado_{ano}_{mes_num}_amazonia",
        "cat": f"categorico_{ano}_{mes_num}_amazonia",
        "filtro": "decendio",
        "total": 3,
        "label": "DECÊNDIO"
    },
    "Quinzena": {
        "acum": f"acumulado_{ano}_{mes_num}_amazonia",
        "cat": f"categorico_{ano}_{mes_num}_amazonia",
        "filtro": "quinzena",
        "total": 2,
        "label": "QUINZENA"
    },
    "Mês": {
        "acum": f"acumulado_{ano}_{mes_num}_amazonia",
        "cat": f"categorico_{ano}_{mes_num}_amazonia",
        "filtro": "mensal",
        "total": 1,
        "label": "MÊS"
    }
}

config = escala_map[escala]

prefix_acum = config["acum"]
prefix_cat  = config["cat"]
total       = config["total"]
label       = config["label"]

# =========================
# CARD
# =========================
def map_card(title, badge, cls, img_base64):
    if img_base64:
        img_html = f'<img src="data:image/png;base64,{img_base64}" />'
    else:
        img_html = '<span style="color:#9CA3AF;font-size:12px">Sem imagem</span>'

    st.markdown(f"""
    <div class="map-card">
        <div class="map-card-header">
            <span>{title}</span>
            <span class="badge {cls}">{badge}</span>
        </div>
        <div class="map-card-body">
            {img_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# GRID
# =========================

imgs_acum = load_images(img_dir, config["acum"], config["filtro"])
imgs_cat  = load_images(img_dir, config["cat"], config["filtro"])

# st.write("PREFIX ACUM:", prefix_acum)
# st.write("PREFIX CAT:", prefix_cat)

# st.write("Arquivos disponíveis:")
# st.write(os.listdir(img_dir))

# st.write("IMG DIR:", img_dir)
# st.write("EXISTE?", os.path.exists(img_dir))

total = min(len(imgs_acum), len(imgs_cat))

for i in range(total):
    c1, c2 = st.columns(2)

    img_acum = imgs_acum[i] if i < len(imgs_acum) else None
    img_cat  = imgs_cat[i] if i < len(imgs_cat) else None

    with c1:
        map_card(
            f"ACUMULADO — {i+1}º PERÍODO" if total > 1 else "ACUMULADO — MENSAL",
            f"{i+1}º {label}" if total > 1 else label,
            "verde",
            img_acum
        )

    with c2:
        map_card(
            f"CATEGÓRICO — {i+1}º PERÍODO" if total > 1 else "CATEGÓRICO — MENSAL",
            f"{i+1}º {label}" if total > 1 else label,
            "ciano",
            img_cat
        )
