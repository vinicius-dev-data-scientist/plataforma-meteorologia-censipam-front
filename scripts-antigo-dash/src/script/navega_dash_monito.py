import os
import base64
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded"
)

if "page" not in st.session_state:
    st.session_state.page = "home"

# =========================
# CAMINHOS BASE
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =========================
# FUNÇÃO LOGO / ÍCONES (BASE64) E FUNÇÃO DE LEITURA DE IMAGEM
# =========================
def load_img_base64(path):
    with open(path, "rb") as img:
        return base64.b64encode(img.read()).decode()

# =========================
# CSS
# =========================
css_path = os.path.join(BASE_DIR, "..", "style", "custom_dash_monitora.css")

with open(css_path, encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# =========================
# ÍCONES SIDEBAR
# =========================
icon_dir = os.path.join(BASE_DIR, "..", "img")

icon_estacoes  = load_img_base64(os.path.join(icon_dir, "icon_estacoes.png"))
icon_satelite  = load_img_base64(os.path.join(icon_dir, "icon_satelite.png"))
icon_modelagem = load_img_base64(os.path.join(icon_dir, "icon_modelagem.png"))
icon_radar     = load_img_base64(os.path.join(icon_dir, "icon_radar.png"))

# =========================
# IMAGENS MAPAS
# =========================

img_dir = os.path.join(BASE_DIR, "..", "img", "OLDS")

def load_images(folder, prefix, filtro):
    images = []

    for f in os.listdir(folder):
        if prefix in f and filtro in f:
            full_path = os.path.join(folder, f)
            images.append(load_img_base64(full_path))

    return sorted(images)

# =========================
# FUNÇÃO LOGO (BASE64)
# =========================
def load_logo_base64(path):
    with open(path, "rb") as img:
        return base64.b64encode(img.read()).decode()

# caminho da logo
logo_path = os.path.join(BASE_DIR, "..", "img", "logo.png")
logo_base64 = load_logo_base64(logo_path)

# =========================
# HEADER
# =========================

components.html(f"""
<style>

.custom-header {{
  position: fixed;
  top: 0;
  left: 0;

  z-index: 9999;
  width: 100%;

  background: white;
  border-bottom: 3px solid #1E9B4E;

  margin: 28px 0 28px 0;
  padding: 20px;
  border-radius: 10px;

  display:flex;
  justify-content:space-between;
  align-items:center;

  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  box-sizing: border-box;
                
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
}}

.custom-header .left {{
  display:flex;
  align-items:center;
  gap:12px;
}}

.custom-header .title {{
  font-weight:700;
  font-size:14px;
  line-height: 1.2;
}}

.custom-header .subtitle {{
  font-size:11px;
  color:#6B7280;
  line-height: 1.2;
}}

.custom-header .right {{
  display:flex;
  align-items:center;
  gap:10px;
}}

.status {{
  background:#E7F6EC;
  color:#15753A;
  padding:6px 12px;
  border-radius:20px;
  font-size:12px;
  font-weight:600;
}}

.clock {{
  background:#E6F7FA;
  padding:6px 12px;
  border-radius:20px;

  font-size:13px;
  font-weight:600;
  color:#0E6B75;

  min-width: 120px;
  text-align: center;

  display: inline-flex;
  align-items: center;
  justify-content: center;

  white-space: nowrap;
}}
</style>

<div class="custom-header">
    <div class="left">
        <img src="data:image/png;base64,{logo_base64}" height="28"/>
        <div class="titles">
            <div class="title">Dashboard de Monitoramento e Previsão</div>
            <div class="subtitle">DIVMET · CRMN — Centro Regional Norte</div>
        </div>
    </div>
    <div class="right">
        <div class="status">● SISTEMA ONLINE</div>
        <div id="clock" class="clock">Carregando...</div>
    </div>
</div>
<script>
function atualizarRelogio() {{
    const el = document.getElementById("clock");
    if (!el) return;

    const agora = new Date();

    const hora = agora.toLocaleTimeString("pt-BR", {{
        timeZone: "America/Sao_Paulo",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    }});

    el.textContent = hora + " BRT";
}}
setTimeout(() => {{
    atualizarRelogio();
    setInterval(atualizarRelogio, 1000);
}}, 200);
</script>
""", height=100)

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
# SIDEBAR
# =========================


with st.sidebar:

    # LOGO EM BASE64 (reaproveita sua função)
    logo_base64 = load_logo_base64(logo_path)

    st.markdown(f"""
    <div class="sidebar-header">
        <img src="data:image/png;base64,{logo_base64}" class="sidebar-logo"/>
        <div class="sidebar-title">DIVISÃO DE METEOROLOGIA</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown(f"""
    <div class="menu">

    <div class="menu-item">
        <div class="menu-title">
        <img src="data:image/png;base64,{icon_estacoes}" class="menu-icon"/>
        Estações
        </div>
        <div class="submenu">
        <div class="submenu-item">INMET — Observações</div>
        </div>
    </div>

    <div class="menu-item">
        <div class="menu-title">
        <img src="data:image/png;base64,{icon_satelite}" class="menu-icon"/>
        Satélite
        </div>
        <div class="submenu">
        <div class="submenu-item">Merge-CPTEC Diário</div>
        <div class="submenu-item">Merge Climatologia</div>
        </div>
    </div>

    <div class="menu-item">
        <div class="menu-title">
        <img src="data:image/png;base64,{icon_modelagem}" class="menu-icon"/>
        Modelagem
        </div>
        <div class="submenu">
        <div class="submenu-item">WRF — Amazônia Legal</div>
        <div class="submenu-item">Modelos Globais</div>
        </div>
    </div>

    <div class="menu-item">
        <div class="menu-title">
        <img src="data:image/png;base64,{icon_radar}" class="menu-icon"/>
        Radar
        </div>
        <div class="submenu">
        <div class="submenu-item">CAPPI — Radar SBMN</div>
        </div>
    </div>

    </div>
    """, unsafe_allow_html=True)


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