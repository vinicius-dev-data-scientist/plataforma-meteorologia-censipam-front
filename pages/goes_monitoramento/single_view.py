# single_view.py

import json
import base64

import streamlit as st
import streamlit.components.v1 as components

from .utils import (
    carregar_imagens,
    format_hora
)

# =====================================================
# SINGLE VIEW
# =====================================================

def render_single_view(config):

    produto = config["produto"]

    data_inicio = config["data_inicio"]

    data_fmt = data_inicio.strftime(
        "%Y%m%d"
    )

    # =================================================
    # CARREGA IMAGENS
    # =================================================

    imagens, opcoes = carregar_imagens(
        produto,
        data_fmt
    )

    if not imagens:

        st.warning(
            "Nenhuma imagem encontrada."
        )

        return

    # =================================================
    # BASE64
    # =================================================

    imagens_b64 = {

        k: (
            "data:image/png;base64,"
            + base64.b64encode(v).decode()
        )

        for k, v in imagens.items()
    }

    js_images = json.dumps(
        imagens_b64
    )

    js_opcoes = json.dumps(
        opcoes
    )

    # =================================================
    # HTML
    # =================================================

    html = f"""
    <html>
    <head>
    <style>
    body {{
        margin: 0;
        padding: 0;
        font-family: sans-serif;
    }}
    .controls {{
        display: flex;
        gap: 10px;
        align-items: center;
        margin-bottom: 12px;
    }}
    .viewer {{
        width: 100%;
        height: 70vh;
        max-height: 700px;
        min-height: 400px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #000;
        border-radius: 12px;
        overflow: hidden;
    }}
    .viewer img {{
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }}
    .info {{
        margin-bottom: 10px;
        font-size: 14px;
        color: #444;
    }}
    </style>
    </head>
    <body>
    <div class="info">
        Produto:
        <b>{produto}</b>
    </div>
    <div class="controls">
        <button id="btn-play">
            ▶ Play
        </button>
        <button id="btn-stop">
            ⏹ Stop
        </button>
        <input
            type="range"
            id="slider"
            min="0"
            max="{len(opcoes)-1}"
            value="{len(opcoes)-1}"
            style="flex:1;"
        >
        <select id="speed">
            <option value="2000">
                🐢 Muito lenta
            </option>
            <option value="1000">
                🐌 Lenta
            </option>
            <option value="500" selected>
                🚶 Normal
            </option>
            <option value="250">
                🚀 Rápida
            </option>
            <option value="100">
                ⚡ Muito rápida
            </option>
        </select>
    </div>
    <div class="info">
        Horário:
        <b id="hora"></b>
    </div>
    <div class="viewer">
        <img id="frame"/>
    </div>
    <script>
    const images = {js_images};
    const opcoes = {js_opcoes};
    const slider = document.getElementById(
        "slider"
    );
    const frame = document.getElementById(
        "frame"
    );
    const hora = document.getElementById(
        "hora"
    );
    const btnPlay = document.getElementById(
        "btn-play"
    );
    const btnStop = document.getElementById(
        "btn-stop"
    );
    const speed = document.getElementById(
        "speed"
    );
    let timer = null;
    // =============================================
    // FRAME
    // =============================================
    function showFrame(idx) {{
        const key = opcoes[idx];
        frame.src = images[key];
        hora.innerHTML =
            key.slice(0,2)
            + ':'
            + key.slice(2)
            + ' UTC';
        slider.value = idx;
    }}
    // =============================================
    // INICIAL
    // =============================================
    showFrame(
        opcoes.length - 1
    );
    // =============================================
    // SLIDER
    // =============================================
    slider.addEventListener(
        "input",
        () => {{
            stopAnim();
            showFrame(
                parseInt(slider.value)
            );
        }}
    );
    // =============================================
    // STOP
    // =============================================
    function stopAnim() {{
        if (timer) {{
            clearInterval(timer);
            timer = null;
        }}
    }}
    // =============================================
    // PLAY
    // =============================================
    function startAnim() {{
        stopAnim();
        let idx = parseInt(
            slider.value
        );
        timer = setInterval(() => {{
            idx++;
            if (
                idx >= opcoes.length
            ) {{
                idx = 0;
            }}
            showFrame(idx);
        }}, parseInt(speed.value));
    }}
    // =============================================
    // BOTÕES
    // =============================================
    btnPlay.addEventListener(
        "click",
        startAnim
    );
    btnStop.addEventListener(
        "click",
        stopAnim
    );
    speed.addEventListener(
        "change",
        () => {{
            if (timer) {{
                startAnim();
            }}
        }}
    );
    </script>
    </body>
    </html>
    """

    components.html(
        html,
        height=850,
        scrolling=False
    )