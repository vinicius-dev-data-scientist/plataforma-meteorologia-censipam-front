# mosaic_view.py

import streamlit as st

from .utils import (
    carregar_imagens,
    PRODUTOS,
    format_hora
)

# =====================================================
# MOSAICO
# =====================================================

def render_mosaic_view(config):

    data_inicio = config["data_inicio"]

    n_linhas = config["n_linhas"]

    # =================================================
    # DATA
    # =================================================

    data_fmt = data_inicio.strftime(
        "%Y%m%d"
    )

    data_label = data_inicio.strftime(
        "%d/%m/%Y"
    )

    # =================================================
    # CARREGA TODOS OS PRODUTOS
    # =================================================

    dados = {}

    for produto in PRODUTOS.keys():

        imagens, opcoes = carregar_imagens(
            produto,
            data_fmt
        )

        dados[produto] = {
            "imagens": imagens,
            "opcoes": opcoes
        }

    # =================================================
    # REFERÊNCIA TEMPORAL
    # usa o primeiro produto válido
    # =================================================

    opcoes_ref = None

    for produto in dados:

        if dados[produto]["opcoes"]:

            opcoes_ref = dados[produto]["opcoes"]

            break

    if not opcoes_ref:

        st.warning(
            "Nenhuma imagem encontrada."
        )

        return

    # =================================================
    # SLIDER TEMPORAL
    # =================================================

    opcoes_formatadas = [
        format_hora(h)
        for h in opcoes_ref
    ]

    hora_escolhida = st.select_slider(
        "Horário",
        options=opcoes_formatadas,
        value=opcoes_formatadas[-1]
    )

    idx = opcoes_formatadas.index(
        hora_escolhida
    )

    chave = opcoes_ref[idx]

    # =================================================
    # HEADER
    # =================================================

    st.markdown(
        f"""
        ### MOSAICO GOES

        📅 {data_label}  
        🕐 {hora_escolhida} UTC
        """
    )

    # =================================================
    # LISTA DE PRODUTOS
    # =================================================

    produtos_lista = list(
        PRODUTOS.keys()
    )

    # =================================================
    # GRID
    # =================================================

    for linha in range(n_linhas):

        cols = st.columns(3)

        for i, produto in enumerate(produtos_lista):

            with cols[i]:

                imagens = dados[produto]["imagens"]

                if chave not in imagens:

                    st.warning(
                        "Sem imagem"
                    )

                    continue

                st.markdown(
                    f"#### {produto}"
                )

                st.image(
                    imagens[chave],
                    use_container_width=True
                )