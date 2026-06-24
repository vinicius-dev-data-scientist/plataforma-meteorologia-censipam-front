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
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
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
        "path": "Classificacao"
    },

    "Geocolor": {
        "slug": "geocolor",
        "path": "Geocolor"
    },

    "Vapor_mid (Banda 9)": {
        "slug": "vapor_mid",
        "path": "Vapor_mid"
    },
    "Clima": {
        "slug": "clima",
        "path": "Clima"
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

@st.cache_data(show_spinner=False)
def carregar_imagens(
    produto,
    data_fmt
):

    produto_info = PRODUTOS[produto]

    # =================================================
    # PATH:
    # img/Figuras/Classificacao/20260602
    # =================================================

    path_produto = os.path.join(
        PATH_IMGS,
        produto_info["path"]
    )

    # DEBUG
    st.write("PATH:", path_produto)

    # =================================================
    # BUSCA PNG
    # =================================================

    busca = os.path.join(
        path_produto,
        data_fmt,
        "*.png"
    )

    #st.write("BUSCA:", busca)

    figs = sorted(
        glob.glob(busca)
    )

    #st.write("TOTAL:", len(figs))

    if figs:
        st.write(figs[:3])

    # =================================================
    # SEM IMAGENS
    # =================================================

    if not figs:
        return {}, []

    imagens = {}

    # =================================================
    # REGEX HORÁRIO
    # =================================================
    # exemplos:
    #
    # Band13_20260602_1810_classificacao.png
    # geocolor_20260602_1940.png
    # vapor_mid_20260602_1930.png
    # =================================================

    padrao = r"_(\d{4})(?:_[^_]*)?\.png$"

    for fig in figs:

        nome = os.path.basename(fig)

        chave = re.findall(
            padrao,
            nome
        )

        if chave:

            # salva apenas o caminho
            imagens[chave[0]] = fig

    return imagens, sorted(imagens.keys())

# =====================================================
# CARREGAR PATHS
# =====================================================

@st.cache_data(show_spinner=False)
def carregar_paths(produto, data_fmt):

    path_produto = os.path.join(
        get_produto_path(produto),
        data_fmt
    )

    busca = os.path.join(
        path_produto,
        "*.png"
    )

    #st.write("BUSCA:", busca)

    figs = sorted(
        glob.glob(busca)
    )

    #st.write("TOTAL:", len(figs))

    if not figs:
        return {}, []

    paths = {}

    padrao = r"_(\d{4})(?:_[^_]*)?\.png$"

    for fig in figs:

        nome = os.path.basename(fig)

        chave = re.findall(
            padrao,
            nome
        )

        if chave:

            paths[chave[0]] = fig

    return paths, sorted(paths.keys())

@st.cache_data(show_spinner=False)
def carregar_clima(ano, mes, dia):

    pasta = os.path.join(
        PATH_IMGS,
        "Clima",
        ano,
        mes,
        dia
        #f"{ano}{mes:02d}{dia:02d}"
    )

    if not os.path.exists(pasta):
        return {}
    
    arquivos = sorted(
        glob.glob(
            os.path.join(
                pasta,
                "*.png"
            )
        )
    )

    grupos = {
        "Vento": [],
        "Evolução": [],
        "Índice": [],
        "Tendência": []
    }

    for arq in arquivos:

        nome = os.path.basename(
            arq
        ).lower()

        if "ventos_" in nome:
            grupos["Vento"].append(arq)
        elif "evolucao_" in nome:
            grupos["Evolução"].append(arq)

        elif (
            "indice" in nome
            or
            "indices" in nome
            or
            "hov_miller" in nome
        ):
            grupos["Índice"].append(arq)

        elif(
            "sst"
            in nome
        ):
            grupos["Tendência"].append(arq)

    return grupos