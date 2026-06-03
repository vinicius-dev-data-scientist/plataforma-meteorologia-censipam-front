# utils.py

import os
import glob
import base64
import regex as re

import streamlit as st

from datetime import datetime


# =====================================================
# BASE DIR
# =====================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

PATH_IMGS = os.path.join(
    BASE_DIR,
    "img",
    "Figuras"
)

# =====================================================
# PRODUTOS
# =====================================================

PRODUTOS = {
    "Classificação": {
        "slug": "classificacao",
        "path": "CLASSIFICACAO"
    },

    "Geocolor": {
        "slug": "geocolor",
        "path": "GEOCOLOR"
    },

    "Vapor_mid (Banda 9)": {
        "slug": "vapor_mid",
        "path": "VAPOR"
    }
}

# =====================================================
# HELPERS
# =====================================================

def format_hora(h):

    return f"{h[:2]}:{h[2:]}"


def to_base64_images(imagens):

    return {
        k: (
            "data:image/png;base64,"
            + base64.b64encode(v).decode()
        )
        for k, v in imagens.items()
    }

# =====================================================
# PATH DO PRODUTO
# =====================================================

def get_produto_path(produto):

    pasta = PRODUTOS[produto]["path"]

    return os.path.join(
        PATH_IMGS,
        pasta
    )

# =====================================================
# DATAS DISPONÍVEIS
# =====================================================

def listar_datas_produto(produto):

    path_produto = get_produto_path(
        produto
    )

    datas = []

    for item in os.listdir(path_produto):

        full_path = os.path.join(
            path_produto,
            item
        )

        if os.path.isdir(full_path):

            datas.append(item)

    return sorted(datas)

# =====================================================
# CARREGAR IMAGENS
# =====================================================

# =====================================================
# CARREGAR IMAGENS
# =====================================================

@st.cache_data(show_spinner=False)
def carregar_imagens(
    produto,
    data_fmt
):

    produto_info = PRODUTOS[produto]

    path_produto = os.path.join(
        PATH_BASE,
        produto_info["path"]
    )

    st.write("PATH:", path_produto)

    busca = os.path.join(
        path_produto,
        f"*{data_fmt}*.png"
    )

    st.write("BUSCA:", busca)

    figs = sorted(
        glob.glob(busca)
    )

    st.write("TOTAL:", len(figs))

    if figs:

        st.write(figs[:3])

    if not figs:
        return {}, []

    imagens = {}

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