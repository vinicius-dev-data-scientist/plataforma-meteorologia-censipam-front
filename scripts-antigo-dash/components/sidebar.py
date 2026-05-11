def render_sidebar():
    import os
    import base64
    import streamlit as st
    from components.style import load_css
    from utils.assets import BASE_DIR, load_img_base64

    load_css()

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    icon_dir = os.path.join(BASE_DIR, "img")

    icon_estacoes  = load_img_base64(os.path.join(icon_dir, "icon_estacoes.png"))
    icon_satelite  = load_img_base64(os.path.join(icon_dir, "icon_satelite.png"))
    icon_modelagem = load_img_base64(os.path.join(icon_dir, "icon_modelagem.png"))
    icon_radar     = load_img_base64(os.path.join(icon_dir, "icon_radar.png"))

    def load_logo_base64(path):
        with open(path, "rb") as img:
            return base64.b64encode(img.read()).decode()

    logo_path = os.path.join(BASE_DIR, "img", "logo.png")
    logo_base64 = load_logo_base64(logo_path)

    with st.sidebar:

        active_page = st.session_state.get("page", "home")

        st.markdown(f"""
        <div class="sidebar-header">
            <img src="data:image/png;base64,{logo_base64}" class="sidebar-logo"/>
            <div class="sidebar-title">DIVISÃO DE METEOROLOGIA</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown(f"""
        <div class="menu">
            <div class="menu-item">
                <div class="menu-title">
                <img src="data:image/png;base64,{icon_estacoes}" class="menu-icon"/>
                Estações
                </div>
                <div class="submenu">
                    <a href="?page=inmet"
                    target="_self"
                    class="submenu-item {'active' if active_page == 'inmet' else ''}">
                    INMET - Observações
                    </a>
                </div>
            </div>
            <div class="menu-item">
                <div class="menu-title">
                <img src="data:image/png;base64,{icon_satelite}" class="menu-icon"/>
                Satélite
                </div>
                <div class="submenu">
                    <a href="?page=merge_climatologia"
                    target="_self"
                    class="submenu-item {'active' if active_page == 'merge_climatologia' else ''}">
                    Merge Climatologia
                    </a>
                    <a href="?page=merge_diario"
                    target="_self"
                    class="submenu-item {'active' if active_page == 'merge_diario' else ''}">
                    Merge-CPTEC Diário
                    </a>
                </div>
            </div>
            <div class="menu-item">
                <div class="menu-title">
                <img src="data:image/png;base64,{icon_modelagem}" class="menu-icon"/>
                Modelagem
                </div>
                <div class="submenu">
                    <div class="submenu-item">WRF — Amazônia Legal</div>
                    <div class="submenu-item">Modelos Globais</div>
                </div>
            </div>
            <div class="menu-item">
                <div class="menu-title">
                <img src="data:image/png;base64,{icon_radar}" class="menu-icon"/>
                Radar
                </div>
                <div class="submenu">
                    <div class="submenu-item">CAPPI — Radar SBMN</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)