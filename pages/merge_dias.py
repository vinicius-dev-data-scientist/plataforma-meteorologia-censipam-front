from datetime import date
import streamlit as st
from utils.assets import load_images, load_images_merge


def map_card(title, badge, cls, img_base64):
    if img_base64:
        img_html = f'<img src="data:image/png;base64,{img_base64}" />'
    else:
        img_html = """
        <div style="color:#9CA3AF; font-size:12px; height:500px; display:flex; align-items:center; justify-content:center; border:1px dashed #DDD; border-radius:4px;">
            Sem imagem cadastrada para este período
        </div>
        """

    st.markdown(
        f"""
        <div class="map-card">
            <div class="map-card-header">
                <span>{title}</span>
                <span class="badge {cls}">{badge}</span>
            </div>
            <div class="map-card-body">
                {img_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def get_image_for_date(data_ref: date):
    """
    Busca a imagem base64 na pasta Merge_Dias correspondente à data selecionada (30_dias).
    """
    data_str = data_ref.strftime("%Y%m%d")
    prefixo_busca = f"{data_str}_30_dias"
    
    lista_imgs = load_images_merge(prefixo_busca, folder_name="Merge_Dias")
    return lista_imgs[0] if lista_imgs else None


def render():
    # =========================
    # TÍTULO
    # =========================
    st.markdown("""
    <div class="main-title">
        Merge · Sequência de Dias Secos/Chuvosos
    </div>
    <div class="subtitle">
        Análise da contagem de dias secos e chuvosos — Amazônia Legal
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # FILTRO POR DIA
    # =========================
    st.markdown('<div class="filter-label">DATA DE REFERÊNCIA</div>', unsafe_allow_html=True)
    data_sel = st.date_input("", value=date.today(), key="data_merge_dias")

    st.markdown("---")

    # =========================
    # CARREGAMENTO DA IMAGEM
    # =========================
    img_dias = get_image_for_date(data_sel)

    if not img_dias:
        st.warning(f"Nenhuma imagem encontrada para {data_sel.strftime('%d/%m/%Y')}.")
        return

    # Renderização da imagem em destaque
    data_formatada = data_sel.strftime("%d/%m/%Y")
    titulo_card = f"<b>DIAS SECOS / CHUVOSOS — {data_formatada}</b>"

    col_center, _ = st.columns([1, 0.01])
    with col_center:
        map_card(titulo_card, "30 DIAS", "ciano", img_dias)