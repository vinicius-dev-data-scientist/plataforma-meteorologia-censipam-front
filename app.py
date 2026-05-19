###################################################################################
## Por que criar app.py?
## O app.py é o ponto de entrada da aplicação Streamlit. Ele é responsável por ## 
## configurar a página, gerenciar o estado da sessão, carregar os componentes de ## estilo e renderizar as páginas com base na navegação do usuário. Ter um arquivo ## separado para isso ajuda a organizar o código e facilita a manutenção da 
## aplicação.
## Ele também atua como um roteador, decidindo qual página renderizar com base na ## navegação do usuário, o que torna a estrutura da aplicação mais clara e modular.
###################################################################################
import streamlit as st

from components.style import load_css
from components.sidebar import render_sidebar
from components.header import render_header
from pages import inmet_dash_plot

# =========================
# CONFIG
# =========================
st.set_page_config(
    #wide para ocupar toda a largura da tela
    layout="wide"
    #initial_sidebar_state="collapsed" para iniciar a barra lateral recolhida
    #initial_sidebar_state="expanded"
)

# st.query_params é um dicionário que contém os parâmetros de consulta da URL. Ele é útil para controlar a navegação e o estado da aplicação com base na URL, permitindo que os usuários compartilhem links específicos para páginas ou estados dentro da aplicação.
query_params = st.query_params

if "page" in query_params:
    st.session_state.page = query_params["page"]

# =========================
# SESSION
# =========================

#session_state é um dicionário que armazena o estado da sessão do usuário. Ele é útil para manter informações persistentes durante a navegação, como a página atual, preferências do usuário ou dados temporários que precisam ser acessados em diferentes partes da aplicação. Ele é especialmente útil para criar uma experiência de usuário mais fluida e personalizada, permitindo que as informações sejam mantidas mesmo quando o usuário navega entre diferentes páginas ou componentes da aplicação.
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
# ROUTER serve para renderizar a página com base na navegação do usuário
# =========================
def render_page(page):

    if page == "merge_climatologia":

        from pages import merge_clima
        merge_clima.render()

    elif page == "merge_diario":

        from services import merge_diario_cptec_service
        merge_diario_cptec_service.render()

    elif page == "inmet":

        from pages import inmet_dash_plot
        inmet_dash_plot.render()

    elif page == "inmet_ranking":

        from pages import inmet_ranking
        inmet_ranking.render()

    elif page == "radar":

        from services import rads_obs_service
        rads_obs_service.render()

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