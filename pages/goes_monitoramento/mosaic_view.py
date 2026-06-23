# mosaic_view.py

import json
import os
import base64

import streamlit as st
import streamlit.components.v1 as components

from .utils import (
    carregar_paths,
    format_hora
)

# =====================================================
# MOSAICO
# =====================================================

def render_mosaic_view(config):

    data_fmt = config[
        "data_inicio"
    ].strftime(
        "%Y%m%d"
    )

    produtos = config[
        "produtos"
    ]

    n_colunas = config[
        "n_colunas"
    ]

    n_linhas = config[
        "n_linhas"
    ]

    # =================================================
    # CARREGA
    # =================================================

    dados = {}

    for produto in produtos:

        paths, opcoes = carregar_paths(
            produto,
            data_fmt
        )

        dados[produto] = {
            "paths": paths,
            "opcoes": opcoes
        }

    # =================================================
    # REFERÊNCIA TEMPORAL
    # =================================================

    opcoes_ref = None

    for p in produtos:

        if dados[p]["opcoes"]:

            opcoes_ref = (
                dados[p]["opcoes"]
            )

            break

    if not opcoes_ref:

        st.warning(
            "Nenhuma imagem encontrada."
        )

        return
    
    # =================================================
    # PATHS PARA JS
    # =================================================

    paths_js = {}

    for produto in produtos:

        paths_js[produto] = {}
        MAX_FRAMES = 5
        for hora, path in list(
            dados[produto]["paths"].items()
        )[-MAX_FRAMES:]:

            with open(path, "rb") as f:

                paths_js[produto][hora] = (
                    "data:image/png;base64,"
                    +
                    base64.b64encode(
                        f.read()
                    ).decode()
                )


    # =================================================
    # GRID
    # =================================================

    total = (
        n_colunas
        * n_linhas
    )

    produtos_render = []

    while len(
        produtos_render
    ) < total:

        produtos_render.extend(
            produtos
        )

    produtos_render = (
        produtos_render[
            :total
        ]
    )

    # =================================================
    # HTML
    # =================================================

    html = f"""

<html>
    <style>
    body {{
        margin:0;
        font-family:sans-serif;
    }}

    .controls{{
        display:flex;
        align-items:center;
        gap:10px;
        margin-bottom:12px;
    }}
    .btn{{
        height:42px;
        min-width:95px;
        border:none;
        border-radius:12px;
        cursor:pointer;
        font-weight:600;
        transition:.2s;
    }}
    .play{{
        background:#1E9B4E;
        color:white;
    }}
    .play:hover{{
        background:#16783c;
    }}
    .stop{{
        background:#EEF2F7;
    }}
    .stop:hover{{
        background:#DDE5EF;
    }}
    .btn:hover {{
        opacity:.9;
    }}
    #slider{{
        flex:1;
        accent-color:#1E9B4E;
    }}
    #speed{{
        height:42px;
        border-radius:12px;
        padding:0 12px;
        border:1px solid #D6DCE5;
        background:white;
    }}
    .grid {{
        display:grid;
        grid-template-columns:
            repeat(
                {n_colunas},
                1fr
            );
        gap:18px;
    }}
    .card {{
        background:white;
        border-radius:14px;
        padding:10px;
            box-shadow:
                0 2px 8px rgba(
                0,0,0,.08
            );
    }}
    .title {{
        font-weight:600;
        margin-bottom:8px;
    }}
    .card img {{
        width:100%;
        height:280px;
        object-fit:contain;
        background:black;
        border-radius:10px;
    }}
    </style>
    <body>
        <div class="controls">
            <button
                class="btn"
                id="play">
                ▶ Iniciar
            </button>
                <button
                class="btn"
                id="stop">
                ⏹ Parar
            </button>
            <input
                type="range"
                id="slider"
                min="0"
                max="{len(opcoes_ref)-1}"
                value="{len(opcoes_ref)-1}"
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
        <div>
            Horário:
            <b id="hora"></b>
        </div>
        <br>
        <div class="grid">
        """
    for i, produto in enumerate(
        produtos_render
    ):

        html += f"""
        <div class="card">
            <div class="title">
                {produto}
            </div>

            <img id="img{i}">
        </div>
        """

    html += f"""
    </div>

    <script>

    const imagens =
    {json.dumps(paths_js)}

    const opcoes =
    {json.dumps(opcoes_ref)}

    const render =
    {json.dumps(produtos_render)}

    const slider =
    document.getElementById(
    "slider"
    )

    const hora =
    document.getElementById(
    "hora"
    )

    const speed =
    document.getElementById(
    "speed"
    )

    const btnPlay =
    document.getElementById(
    "play"
    )

    const btnStop =
    document.getElementById(
    "stop"
    )

    let timer = null

    function show(idx){{

        const chave =
            opcoes[idx]

        hora.innerHTML =
            chave.slice(0,2)
            + ':'
            + chave.slice(2)
            + ' UTC'

        slider.value =
            idx

        render.forEach(
            (
                produto,
                i
            )=>{{

                const img =
                    document.getElementById(
                        "img"+i
                    )

                if(
                    imagens[produto]
                    &&
                    imagens[produto][chave]
                ){{

                    img.src =
                        imagens[produto][chave]

                }}else{{

                    img.src = ""

                }}

            }}
        )

    }}

    show(
    opcoes.length-1
    )

    slider.addEventListener(
    'input',
    ()=>{{
    stop()
    show(
    parseInt(
    slider.value
    )
    )
    }}
    )

    function stop(){{
    clearInterval(timer)
    timer=null
    }}

    function play(){{

    stop()

    let idx =
    parseInt(
    slider.value
    )

    timer =
    setInterval(
    ()=>{{

    idx++

    if(
    idx
    >=
    opcoes.length
    )
    idx=0

    show(
    idx
    )

    }},
    parseInt(
    speed.value
    )
    )

    }}

    btnPlay.onclick =
    play

    btnStop.onclick =
    stop

    speed.onchange =
    ()=>{{
    if(timer)
    play()
    }}

    </script>

    </body>
    </html>
    """
    components.html(
        html,
        height=(
            380
            *
            n_linhas
        )
        +
        120,
        scrolling=False
    )