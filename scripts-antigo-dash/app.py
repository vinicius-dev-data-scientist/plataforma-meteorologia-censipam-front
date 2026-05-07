import streamlit as st

from components.style import load_css
from components.sidebar import render_sidebar
from components.header import render_header

# =========================
# CONFIG
# =========================
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded"
)

query_params = st.query_params

if "page" in query_params:
    st.session_state.page = query_params["page"]

# =========================
# SESSION
# =========================
if "page" not in st.session_state:
    st.session_state.page = "home"

# =========================
# CSS
# =========================
load_css()

# =========================
# COMPONENTS
# =========================
render_header()
render_sidebar()

# =========================
# ROUTER
# =========================
def render_page(page):

    if page == "merge_climatologia":

        from pages import merge_clima
        merge_clima.render()

    elif page == "merge_diario":

        from services import merge_diario_cptec
        merge_diario_cptec.render()

    elif page == "inmet":

        from services import inmet_dash
        inmet_dash.render()

    elif page == "radar":

        from services import rads_obs
        rads_obs.render()

    else:

        st.markdown("""
            <div class="main-title">
                Censipam · Divisão de Meteorologia
            </div>
            <div class="subtitle">
                Dashboard de visualização de dados meteorológicos
            </div>
        """, unsafe_allow_html=True)

# =========================
# RUN PAGE
# =========================
render_page(st.session_state.page)