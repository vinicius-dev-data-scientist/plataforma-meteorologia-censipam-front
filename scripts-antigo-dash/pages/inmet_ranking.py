import streamlit as st
import plotly.graph_objects as go

from services.inmet_dash_service import (
    load_station_data,
    filter_period
)

# =========================
# ESTAÇÕES
# =========================

stations = {

    "MANAUS (A101)": "MANAUS.csv",
    "BARCELOS (A128)": "BARCELOS.csv",
    "BOCA DO ACRE (A110)": "BOCA_DO_ACRE.csv",
    "COARI (A117)": "COARI.csv",
    "HUMAITÁ (A112)": "HUMAITA.csv",
    "ITACOATIARA (A121)": "ITACOATIARA.csv",
    "MANACAPURU (A119)": "MANACAPURU.csv",
    "MANICORÉ (A133)": "MANICORE.csv",
    "NOVO ARIPUANÃ (A144)": "NOVO_ARIPUANÃ.csv",
    "PARINTINS (A123)": "PARINTINS.csv",
    "SÃO GABRIEL DA CACHOEIRA (A134)": "SGCACHOEIRA.csv",
    "URUCARÁ (A124)": "URUCARÁ.csv"
}

# =========================
# RENDER
# =========================

def render():

    st.markdown("""
    <div class="main-title">
        INMET - Ranking
    </div>

    <div class="subtitle">
        Ranking meteorológico entre estações
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # FILTROS
    # =========================

    c1, c2 = st.columns([2,1])

    with c1:

        st.markdown(
            '<div class="filter-label">PERÍODO</div>',
            unsafe_allow_html=True
        )

        period = st.selectbox(
            "",
            [
                "Últimos 30 dias",
                "Últimos 15 dias",
                "Este mês"
            ]
        )

    with c2:

        st.markdown(
            '<div class="filter-label">VARIÁVEL</div>',
            unsafe_allow_html=True
        )

        variavel = st.selectbox(
            "",
            [
                "Maior Temperatura",
                "Maior Precipitação",
                "Maior Rajada"
            ]
        )

    # =========================
    # PROCESSA DADOS
    # =========================

    ranking_data = []

    for station_name, file_name in stations.items():

        try:

            df = load_station_data(file_name)

            df = filter_period(df, period)

            if df.empty:
                continue

            cidade = station_name.split(" (")[0]

            # =========================
            # TEMPERATURA
            # =========================

            if variavel == "Maior Temperatura":

                valor = df["temp_max"].max()

                unidade = "°C"

            # =========================
            # PRECIPITAÇÃO
            # =========================

            elif variavel == "Maior Precipitação":

                valor = df["chuva"].sum()

                unidade = "mm"

            # =========================
            # RAJADA
            # =========================

            else:

                valor = df["vento_raj"].max()

                unidade = "m/s"

            ranking_data.append({

                "cidade": cidade,
                "valor": round(valor, 1),
                "unidade": unidade
            })

        except:
            pass

    # =========================
    # ORDENA
    # =========================

    ranking_data = sorted(
        ranking_data,
        key=lambda x: x["valor"],
        reverse=True
    )

    # =========================
    # DATAFRAME
    # =========================

    st.markdown("### Ranking Geral")

    for idx, item in enumerate(ranking_data, start=1):

        medalha = "🥇"

        if idx == 2:
            medalha = "🥈"

        elif idx == 3:
            medalha = "🥉"

        st.markdown(
            f"""
            <div style="
                background:white;
                border-radius:14px;
                padding:18px;
                margin-bottom:12px;
                box-shadow:0 2px 8px rgba(0,0,0,.05);
                border-left:5px solid #1E9B4E;
            ">
                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                ">
                    <div style="
                        font-size:18px;
                        font-weight:700;
                        color:#111827;
                    ">
                        {medalha} #{idx} · {item['cidade']}
                    </div>
                    <div style="
                        font-size:28px;
                        font-weight:800;
                        color:#1E9B4E;
                    ">
                        {item['valor']} {item['unidade']}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # =========================
    # GRÁFICO
    # =========================

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=[x["cidade"] for x in ranking_data],

            y=[x["valor"] for x in ranking_data],

            text=[
                f'{x["valor"]} {x["unidade"]}'
                for x in ranking_data
            ],

            textposition="outside",

            marker=dict(
                color="#1E9B4E"
            )
        )
    )

    fig.update_layout(

        title=dict(
            text=variavel.upper(),
            x=0
        ),

        height=450,

        paper_bgcolor="white",
        plot_bgcolor="white",

        margin=dict(
            l=10,
            r=10,
            t=60,
            b=10
        ),

        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(0,0,0,.05)"
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )