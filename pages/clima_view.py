from datetime import datetime
import os
import base64
import streamlit as st

from .goes_monitoramento.utils import carregar_clima


def img64(path):

    with open(
        path,
        "rb"
    ) as f:

        return (
            "data:image/png;base64,"
            +
            base64.b64encode(
                f.read()
            ).decode()
        )


def render():

    data = st.date_input(
        "Data",
        value=datetime.today()
    )

    grupos = carregar_clima(

        str(data.year),

        f"{data.month:02}",

        f"{data.day:02}"

    )

    if not grupos:

        st.warning(
            "Nenhuma imagem encontrada."
        )

        return

    ordem = [

        "Vento",
        "Evolução",
        "Índice",
        "Tendência"

    ]

    for categoria in ordem:

        imagens = grupos[
            categoria
        ]

        if not imagens:
            continue

        st.subheader(
            categoria
        )

        cols = st.columns(
            min(
                3,
                len(imagens)
            )
        )

        for i, path in enumerate(
            imagens
        ):

            with cols[
                i
                %
                len(cols)
            ]:

                st.image(
                    path,

                    caption=os.path.basename(
                        path
                    ).replace(
                        ".png",
                        ""
                    ),

                    use_container_width=True
                )