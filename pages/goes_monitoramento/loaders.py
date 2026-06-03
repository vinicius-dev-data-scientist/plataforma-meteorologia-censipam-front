import streamlit as st
import streamlit.components.v1 as components

import regex as re
import glob
import os
import base64
import json

from datetime import datetime

from pages.goes_monitoramento.utils import PATH_IMGS

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