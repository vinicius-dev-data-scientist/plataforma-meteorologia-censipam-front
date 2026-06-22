# controls.py

import streamlit as st

from datetime import datetime

from .utils import PRODUTOS

# =====================================================
# CONTROLES
# =====================================================

def render_controls():
    # =====================================================
    # MODO
    # =====================================================

    modo = st.radio(
        "Modo de visualização",
        [
            "Visualização única",
            "Mosaico"
        ],
        horizontal=True,
        key="gm_modo_visualizacao"
    )

    # =====================================================
    # PERÍODO
    # =====================================================

    col_ini, col_fim = st.columns(2)

    with col_ini:

        data_inicio = st.date_input(
            "Data inicial",
            value=datetime.today(),
            max_value=datetime.today(),
            key="gm_data_inicio"
        )

    with col_fim:

        data_fim = st.date_input(
            "Data final",
            value=datetime.today(),
            max_value=datetime.today(),
            key="gm_data_fim"
        )

    # =====================================================
    # VALIDAÇÃO
    # =====================================================

    if data_inicio > data_fim:

        st.warning(
            "A data inicial não pode ser maior que a data final."
        )

        st.stop()

    # =====================================================
    # VISUALIZAÇÃO ÚNICA
    # =====================================================

    produto = None
    n_linhas = None

    if modo == "Visualização única":

        produto = st.selectbox(
            "Produto",
            list(PRODUTOS.keys()),
            index=0,
            key="gm_produto"
        )

    # =====================================================
    # MOSAICO
    # =====================================================

    else:

        produtos = st.multiselect(
            "Produtos",
            options=list(PRODUTOS.keys()),
            default=list(PRODUTOS.keys()),
            key="gm_produtos"
        )

        col1, col2 = st.columns(2)

        with col1:

            n_colunas = st.number_input(
                "Número de colunas",
                min_value=1,
                max_value=4,
                value=3,
                step=1,
                key="gm_n_colunas"
            )

        with col2:

            n_linhas = st.number_input(
                "Número de linhas",
                min_value=1,
                max_value=10,
                value=2,
                step=1,
                key="gm_n_linhas"
            )

        if not produtos:

            st.warning(
                "Selecione pelo menos um produto."
            )

            st.stop()

    # =====================================================
    # RETORNO
    # =====================================================

    return {

        "modo": modo,

        "produto": produto,

        "produtos": (
            produtos
            if modo == "Mosaico"
            else [produto]
        ),

        "data_inicio": data_inicio,

        "data_fim": data_fim,

        "n_colunas": (
            n_colunas
            if modo == "Mosaico"
            else 1
        ),

        "n_linhas": n_linhas
    }