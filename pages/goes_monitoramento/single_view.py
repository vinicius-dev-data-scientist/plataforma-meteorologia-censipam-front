# single_view.py

import streamlit as st

from .utils import (
    carregar_imagens,
    to_base64_images,
    format_hora
)

# =====================================================
# SINGLE VIEW
# =====================================================

def render_single_view(config):

    produto = config["produto"]

    data_inicio = config["data_inicio"]

    # =================================================
    # FORMATA DATA
    # =================================================

    data_fmt = data_inicio.strftime(
        "%Y%m%d"
    )

    data_label = data_inicio.strftime(
        "%d/%m/%Y"
    )

    # =================================================
    # CARREGA IMAGENS
    # =================================================

    imagens, opcoes = carregar_imagens(
        produto,
        data_fmt
    )

    # =================================================
    # SEM IMAGENS
    # =================================================

    if not imagens:

        st.warning(
            f"Nenhuma imagem encontrada para {data_label}."
        )

        return

    # =================================================
    # INFO
    # =================================================

    st.success(
        f"{len(imagens)} imagens carregadas."
    )

    # =================================================
    # CONVERTE BASE64
    # =================================================

    imagens_b64 = to_base64_images(
        imagens
    )

    # =================================================
    # SIDEBAR TEMPORAL
    # =================================================

    opcoes_formatadas = [
        format_hora(h)
        for h in opcoes
    ]

    hora_escolhida = st.select_slider(
        "Horário",
        options=opcoes_formatadas,
        value=opcoes_formatadas[-1]
    )

    # =================================================
    # OBTÉM CHAVE ORIGINAL
    # =================================================

    idx = opcoes_formatadas.index(
        hora_escolhida
    )

    chave = opcoes[idx]

    # =================================================
    # HEADER
    # =================================================

    st.markdown(
        f"""
        ### {produto}

        📅 {data_label}  
        🕐 {hora_escolhida} UTC
        """
    )

    # =================================================
    # EXIBE IMAGEM
    # =================================================

    st.image(
        imagens[chave],
        use_container_width=True
    )

    # =================================================
    # DEBUG
    # =================================================

    with st.expander(
        "Informações"
    ):

        st.write(
            {
                "produto": produto,
                "data": data_fmt,
                "frames": len(opcoes),
                "frame_atual": chave
            }
        )