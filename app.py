###################################################################################
# app.py
#
# Ponto de entrada da aplicação Streamlit
#
# Responsabilidades:
# - Configurar a página (layout, sidebar, etc.)
# - Carregar estilos globais (CSS)
# - Gerenciar o estado da sessão (session_state)
# - Renderizar componentes globais (header e sidebar)
# - Atuar como roteador, decidindo qual página exibir
#
# Ter esse arquivo separado:
# - Centraliza a configuração da aplicação
# - Facilita manutenção e escalabilidade
# - Deixa as páginas desacopladas da lógica principal
###################################################################################

import streamlit as st

# Componentes reutilizáveis
from components.style import load_css
from components.sidebar import render_sidebar
from components.header import render_header


# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
# Define configurações globais da aplicação Streamlit
st.set_page_config(
    layout="wide",  # Ocupa toda a largura da tela
    # initial_sidebar_state="collapsed",  # Inicia com sidebar recolhida (opcional)
    # initial_sidebar_state="expanded"   # Inicia com sidebar aberta (opcional)
)


# ==============================================================================
# CONTROLE DE NAVEGAÇÃO VIA URL
# ==============================================================================
# st.query_params permite ler parâmetros da URL
# Exemplo: ?page=inmet
query_params = st.query_params

# Se existir o parâmetro "page" na URL,
# ele sobrescreve o valor atual da sessão
if "page" in query_params:
    st.session_state.page = query_params["page"]


# ==============================================================================
# GERENCIAMENTO DE SESSÃO
# ==============================================================================
# st.session_state armazena informações persistentes da sessão do usuário
# Aqui garantimos que sempre exista uma página definida
if "page" not in st.session_state:
    st.session_state.page = "home"


# ==============================================================================
# ESTILOS (CSS)
# ==============================================================================
# Carrega estilos globais da aplicação
load_css()


# ==============================================================================
# COMPONENTES GLOBAIS
# ==============================================================================
# Renderiza componentes fixos da interface
render_header()
render_sidebar()


# ==============================================================================
# ROUTER
# ==============================================================================
# Responsável por decidir qual página será renderizada
# com base no valor de st.session_state.page
def render_page(page: str):
    """
    Renderiza a página correspondente à navegação atual.

    Args:
        page (str): identificador da página
    """

    if page == "merge_climatologia":
        from pages import merge_clima
        merge_clima.render()

    elif page == "merge_diario":
        from pages import merge_diario_cptec
        merge_diario_cptec.render()

    elif page == "clima":
        from pages import clima_view
        clima_view.render()

    elif page == "goes_monitoramento":
        from pages import goes_monitoramento
        goes_monitoramento.render()

    elif page == "inmet":
        from pages import inmet_dash_plot
        inmet_dash_plot.render()

    elif page == "inmet_ranking":
        from pages import inmet_ranking
        inmet_ranking.render()
        
    elif page == "merge_acumulado":
        from pages import merge_acumulado
        merge_acumulado.render()
    
    elif page == "merge_dias":
        from pages import merge_dias
        merge_dias.render()

    elif page == "radar":
        from pages import rads_obs2
        rads_obs2.render()

    else:
        # Página inicial / fallback
        st.markdown(
            """
            <div class="main-title">
                Censipam · Divisão de Meteorologia
            </div>
            <div class="subtitle">
                Dashboard de visualização de dados meteorológicos
            </div>
            """,
            unsafe_allow_html=True
        )


# ==============================================================================
# EXECUÇÃO
# ==============================================================================
# Renderiza a página atual armazenada na sessão
render_page(st.session_state.page)