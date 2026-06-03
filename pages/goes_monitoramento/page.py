# page.py

import streamlit as st

from .controls import render_controls

from .single_view import render_single_view
from .mosaic_view import render_mosaic_view

# =====================================================
# PAGE
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

    # =================================================
    # CONTROLES
    # =================================================

    config = render_controls()

    # =================================================
    # RENDER
    # =================================================

    if config["modo"] == "Visualização única":

        render_single_view(config)

    else:

        render_mosaic_view(config)