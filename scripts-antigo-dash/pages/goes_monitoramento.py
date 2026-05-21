import streamlit as st
import streamlit.components.v1 as components

import regex as re
import glob
import os
import base64
import json

from datetime import datetime

# =====================================================
# PATH DAS IMAGENS
# =====================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

PATH_IMGS = os.path.join(
    BASE_DIR,
    "img",
    "FIGS_CAPPI",
    "FIGS_CAPPI"
)

# =====================================================
# CACHE
# =====================================================

@st.cache_data(show_spinner="📡 Carregando imagens...")
def carregar_imagens(data_fmt: str):

    figs = sorted(
        glob.glob(
            os.path.join(
                PATH_IMGS,
                f"*{data_fmt}*.png"
            )
        )
    )

    if not figs:
        return {}, []

    imagens = {}

    # exemplo:
    # cappi_CZ_03000_20260519_0036.png
    padrao = r"_(\d{4})\.png$"

    for fig in figs:

        chave = re.findall(
            padrao,
            fig
        )

        if chave:

            with open(fig, "rb") as f:

                imagens[chave[0]] = f.read()

    return imagens, sorted(imagens.keys())

# =====================================================
# RENDER
# =====================================================

def render():

    st.markdown("""
    <div class="main-title">
        GOES - Monitoramento
    </div>
    <div class="subtitle">
        Time lapse das imagens de satélite
    </div>
    """, unsafe_allow_html=True)

    # =====================================================
    # CONTROLES
    # =====================================================

    n_fig_fix = 2

    with st.container(border=True):

        col_b, col_d = st.columns([0.30, 0.70])

        # =====================================================
        # COLUNA ESQUERDA
        # =====================================================

        with col_b:

            bandas = [
                "CAPPI CZ 3km",
                "CAPPI Classificação"
            ]

            st.markdown(
                '<div class="filter-label">PRODUTO</div>',
                unsafe_allow_html=True
            )

            prod = st.selectbox(
                "",
                bandas,
                index=0
            )

            st.markdown(
                '<div class="filter-label">DATA</div>',
                unsafe_allow_html=True
            )

            data = st.date_input(
                "",
                format="DD/MM/YYYY",
                max_value=datetime.today()
            )

            data_fmt = data.strftime("%Y%m%d")
            data_label = data.strftime("%d/%m/%Y")

            imagens, opcoes = carregar_imagens(
                data_fmt
            )

            if not imagens:

                st.warning(
                    f"⚠️ Nenhuma imagem encontrada para {data_label}"
                )

                st.stop()

            opcoes_formatadas = [
                f"{h[:2]}:{h[2:]}"
                for h in opcoes
            ]

            n_total = len(opcoes)

        # =====================================================
        # COLUNA DIREITA
        # =====================================================

        with col_d:

            st.markdown(
                '<div class="filter-label">JANELA DA ANIMAÇÃO</div>',
                unsafe_allow_html=True
            )

            loop = st.radio(
                "",
                [
                    "Por período",
                    f"As últimas {n_fig_fix} imagens"
                ],
                horizontal=True
            )

            # =====================================================
            # LOOP POR PERÍODO
            # =====================================================

            if loop == "Por período":

                idx_inicio, idx_fim = st.select_slider(
                    "",
                    options=opcoes_formatadas,
                    value=(
                        opcoes_formatadas[0],
                        opcoes_formatadas[-1]
                    ),
                    label_visibility="collapsed"
                )

                h_ini = opcoes_formatadas.index(
                    idx_inicio
                )

                h_fim = opcoes_formatadas.index(
                    idx_fim
                )

                n_selecionadas = (
                    h_fim - h_ini
                ) + 1

                opcoes_loop = opcoes[
                    h_ini:h_fim + 1
                ]

                st.caption(
                    f"""
                    Loop de {idx_inicio} UTC
                    até {idx_fim} UTC
                    — {n_selecionadas} de {n_total} imagens
                    """
                )

            # =====================================================
            # LOOP ÚLTIMAS IMAGENS
            # =====================================================

            else:

                n_selecionadas = n_fig_fix

                opcoes_loop = opcoes[
                    -n_fig_fix:
                ]

                st.caption(
                    f"""
                    Loop de {opcoes[-n_fig_fix]} UTC
                    até {opcoes[-1]} UTC
                    — {n_selecionadas} de {n_total} imagens
                    """
                )

    # =====================================================
    # BASE64
    # =====================================================

    img_uris_all = {

        k: (
            "data:image/png;base64," +
            base64.b64encode(v).decode()
        )

        for k, v in imagens.items()
    }

    js_images_all = json.dumps(
        img_uris_all
    )

    js_opcoes_all = json.dumps(
        opcoes
    )

    js_opcoes_loop = json.dumps(
        opcoes_loop
    )

    # =====================================================
    # HTML
    # =====================================================

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
/>
<script
    src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
</script>
<script src="https://html2canvas.hertzen.com/dist/html2canvas.min.js"></script>
<style>
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}
    body {{
        font-family: sans-serif;
        background: transparent;
    }}
    .info-bar {{
        display: flex;
        align-items: center;
        gap: 1rem;
        background: white;
        border-radius: 14px;
        padding: 14px 18px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,.05);
        border-left: 5px solid #1E9B4E;
        font-size: 14px;
        color: #374151;
    }}
    .info-bar b {{
        color: #111827;
    }}
    .info-bar .ct {{
        margin-left: auto;
        color: #6B7280;
        font-size: 12px;
    }}
    .controls {{
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 14px;
        flex-wrap: wrap;
    }}
    #slider {{
        flex: 1;
        accent-color: #1E9B4E;
    }}
    .btn {{
        padding: 8px 14px;
        border: none;
        border-radius: 10px;
        cursor: pointer;
        font-size: 13px;
        font-weight: 600;
    }}
    .btn-play {{
        background: #1E9B4E;
        color: white;
    }}
    .btn-stop {{
        background: #E5E7EB;
    }}
    .btn-dl {{
        background: #111827;
        color: white;
    }}
    select {{
        padding: 8px 10px;
        border-radius: 10px;
        border: 1px solid #D1D5DB;
    }}
    #map {{
        width: 100%;
        height: 760px;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 14px rgba(0,0,0,.08);
    }}
    .caption {{
        text-align: center;
        font-size: 12px;
        color: #6B7280;
        margin-top: 8px;
    }}

    .map-tiles {{
        image-rendering: auto !important;
    }}

    .leaflet-tile {{
        border: 0 !important;
        outline: 0 !important;

        /* remove gaps entre tiles */
        width: 256.5px !important;
        height: 256.5px !important;
    }}

    .leaflet-container {{
        background: #fff;
    }}

    .leaflet-pane,
    .leaflet-tile-container {{
        transform: translate3d(0,0,0);
    }}
    .leaflet-container {{
        background: #ffffff;
    }}

    .leaflet-tile {{
        border: none !important;
        outline: none !important;
        image-rendering: auto !important;
    }}

    .leaflet-container img {{
        max-width: none !important;
    }}

    .leaflet-pane {{
        z-index: 400;
    }}

    .leaflet-image-layer {{
        image-rendering: auto !important;
        interpolation-mode: bicubic;
        border: none !important;
    }}
</style>
</head>
<body>
<div class="info-bar">
    <span>
        📅 <b>{data_label}</b>
    </span>
    <span>
        🕐 <b id="hora-lbl">--:-- UTC</b>
    </span>
    <span class="ct" id="frame-lbl"></span>
</div>
<div class="controls">
    <input
        type="range"
        id="slider"
        min="0"
        max="{n_total - 1}"
        value="{n_total - 1}"
    >
    <button
        class="btn btn-play"
        id="btn-play"
    >
        ▶ Iniciar
    </button>
    <button
        class="btn btn-stop"
        id="btn-stop"
    >
        ⏹ Parar
    </button>
    <select id="vel-sel">
        <option value="2.0">
            🐢 Muito lenta
        </option>
        <option value="1.0">
            🐌 Lenta
        </option>
        <option value="0.5" selected>
            🚶 Normal
        </option>
        <option value="0.25">
            🚀 Rápida
        </option>
        <option value="0.1">
            ⚡ Muito rápida
        </option>
    </select>
    <button
        class="btn btn-dl"
        id="btn-dl"
    >
        ⬇
    </button>
</div>
<div id="map"></div>
<p class="caption" id="caption"></p>
<script>
    const imagesAll  = {js_images_all};
    const opcoesAll  = {js_opcoes_all};
    const opcoesLoop = {js_opcoes_loop};
    const dtLabel = "{data_label}";
    const fmtH = h =>
        h.slice(0,2)
        + ':'
        + h.slice(2)
        + ' UTC';
    // =====================================================
    // LEAFLET
    // =====================================================
    const bounds = [
        [-5.4564, -62.3126],
        [-0.8221, -57.6701]
    ];
    const map = L.map('map', {{
        zoomControl: true,
        preferCanvas: true
    }});
    map.fitBounds(bounds);
    L.tileLayer(
        'https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
        {{
            attribution: '&copy; OpenStreetMap',

            // remove artefatos
            detectRetina: false,
            updateWhenIdle: true,
            updateWhenZooming: false,
            keepBuffer: 0,

            // suavização
            tileSize: 256,
            zoomOffset: 0,

            // importante
            className: 'map-tiles'
        }}
    ).addTo(map);
    let overlay = null;
    // =====================================================
    // ELEMENTOS
    // =====================================================
    const slider = document.getElementById('slider');
    const horaLbl = document.getElementById(
        'hora-lbl'
    );
    const frameLbl = document.getElementById(
        'frame-lbl'
    );
    const caption = document.getElementById(
        'caption'
    );
    const btnPlay = document.getElementById(
        'btn-play'
    );
    const btnStop = document.getElementById(
        'btn-stop'
    );
    const btnDl = document.getElementById(
        'btn-dl'
    );
    const velSel = document.getElementById(
        'vel-sel'
    );
    let timer = null;
    let loopIdx = 0;
    // =====================================================
    // FRAME
    // =====================================================
    function showFrame(globalIdx) {{
        const key = opcoesAll[globalIdx];
        if (overlay) {{
            map.removeLayer(overlay);
        }}
        overlay = L.imageOverlay(
            imagesAll[key],
            bounds,
            {{
                opacity: 0.65,
                interactive: false,
                crossOrigin: true
            }}
        ).addTo(map);
        horaLbl.textContent = fmtH(key);
        slider.value = globalIdx;
        frameLbl.textContent =
            (globalIdx + 1)
            + ' / '
            + opcoesAll.length
            + (timer ? ' ▶' : '');
        caption.textContent =
            'CAPPI • '
            + dtLabel
            + ' '
            + fmtH(key);
    }}
    // =====================================================
    // FRAME INICIAL
    // =====================================================
    showFrame(
        opcoesAll.length - 1
    );
    // =====================================================
    // SLIDER
    // =====================================================
    slider.addEventListener(
        'input',
        () => {{
            stopAnim();
            showFrame(
                parseInt(slider.value)
            );
        }}
    );
    // =====================================================
    // STOP
    // =====================================================
    function stopAnim() {{
        if (timer) {{
            clearInterval(timer);
            timer = null;
        }}
        btnPlay.textContent =
            '▶ Iniciar';
    }}
    // =====================================================
    // START
    // =====================================================
    function startAnim() {{
        stopAnim();
        const curKey = opcoesAll[
            parseInt(slider.value)
        ];
        const li =
            opcoesLoop.indexOf(curKey);
        loopIdx = li >= 0 ? li : 0;
        const ms =
            parseFloat(velSel.value)
            * 1000;
        timer = setInterval(() => {{
            loopIdx =
                (loopIdx + 1)
                % opcoesLoop.length;
            const globalIdx =
                opcoesAll.indexOf(
                    opcoesLoop[loopIdx]
                );
            showFrame(globalIdx);
        }}, ms);
        btnPlay.textContent =
            '⏸ Pausar';
    }}
    // =====================================================
    // BOTÕES
    // =====================================================
    btnPlay.addEventListener(
        'click',
        () => timer
            ? stopAnim()
            : startAnim()
    );
    btnStop.addEventListener(
        'click',
        stopAnim
    );
    velSel.addEventListener(
        'change',
        () => {{
            if (timer)
                startAnim();
        }}
    );
    // =====================================================
    // DOWNLOAD MAPA + OVERLAY
    // =====================================================

    btnDl.addEventListener(
        'click',
        async () => {{

            const key = opcoesAll[
                parseInt(slider.value)
            ];

            const mapDiv =
                document.getElementById('map');

            const canvas =
                await html2canvas(mapDiv, {{
                    useCORS: true,
                    allowTaint: true,
                    backgroundColor: null
                }});

            const link =
                document.createElement('a');

            link.download =
                'CAPPI_{data_fmt}_'
                + key
                + '.png';

            link.href =
                canvas.toDataURL('image/png');

            link.click();
        }}
    );
</script>
</body>
</html>
"""

    components.html(
        html,
        height=950,
        scrolling=False
    )