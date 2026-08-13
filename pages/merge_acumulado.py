from datetime import date
import streamlit as st
from utils.assets import load_images_merge


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


def get_image_for_date_and_scale(data_ref: date, escala: str):
    escala_map = {
        "Dia Corrente": "1_dias",
        "Últimos 7 dias": "7_dias",
        "Últimos 15 dias": "15_dias",
        "Último Mês": "30_dias"
    }

    sufixo_dias = escala_map.get(escala, "1_dias")
    data_str = data_ref.strftime("%Y%m%d")
    
    # Monta o prefixo exato: YYYYMMDD_X_dias
    prefixo_busca = f"{data_str}_{sufixo_dias}"
    
    lista_imgs = load_images_merge(prefixo_busca, folder_name="Merge_Acumulado")
    
    return lista_imgs[0] if lista_imgs else None


def render():
    # =========================
    # TÍTULO
    # =========================
    st.markdown("""
    <div class="main-title">
        Merge · Acumulado
    </div>
    <div class="subtitle">
        Análise por dia corrente · 7 dias · 15 dias · último mês — Amazônia Legal
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # FILTROS GLOBAIS
    # =========================
    c1, c2 = st.columns([2, 3])

    with c1:
        st.markdown('<div class="filter-label">DATA DE REFERÊNCIA</div>', unsafe_allow_html=True)
        data_sel = st.date_input("", value=date.today(), key="data_acumulado")

    with c2:
        st.markdown('<div class="filter-label">ESCALA TEMPORAL</div>', unsafe_allow_html=True)
        escala = st.radio(
            "", 
            ["Dia Corrente", "Últimos 7 dias", "Últimos 15 dias", "Último Mês"], 
            horizontal=True,
            key="escala_acumulado"
        )

    st.markdown("---")

    # =========================
    # CARREGAMENTO DA IMAGEM
    # =========================
    img_acum = get_image_for_date_and_scale(data_sel, escala)

    if not img_acum:
        st.warning(f"Nenhuma imagem encontrada para {data_sel.strftime('%d/%m/%Y')} no período selecionado ({escala}).")
        return

    # Renderização da imagem em destaque
    badge_label = escala.upper()
    data_formatada = data_sel.strftime("%d/%m/%Y")
    titulo_card = f"<b>ACUMULADO DE PRECIPITAÇÃO — {data_formatada}</b>"

    col_center, _ = st.columns([1, 0.01])
    with col_center:
        map_card(titulo_card, badge_label, "verde", img_acum)