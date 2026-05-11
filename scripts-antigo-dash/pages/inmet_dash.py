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
    "COARI (A117)": "COARI.csv",
    "PARINTINS (A123)": "PARINTINS.csv",
}

# =========================
# CARD KPI
# =========================

def metric_card(
    title,
    value,
    unit,
    extra,
    color
):

    st.markdown(
        f"""
        <div style="
            background:white;
            border-radius:14px;
            padding:18px;
            border-top:4px solid {color};
            box-shadow:0 2px 8px rgba(0,0,0,.05);
            min-height:120px;
        ">
            <div style="
                font-size:11px;
                letter-spacing:.12em;
                color:#9CA3AF;
                font-weight:700;
                text-transform:uppercase;
            ">
                {title}
            </div>
            <div style="
                margin-top:10px;
                font-size:42px;
                font-weight:700;
                color:#111827;
                line-height:1;
            ">
                {value}
                <span style="
                    font-size:22px;
                    color:#6B7280;
                    font-weight:600;
                ">
                    {unit}
                </span>
            </div>
            <div style="
                margin-top:10px;
                font-size:13px;
                color:#9CA3AF;
            ">
                {extra}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================
# RENDER
# =========================

def render():

    # =========================
    # TÍTULO
    # =========================

    st.markdown("""
    <div class="main-title">
        Estações INMET
    </div>

    <div class="subtitle">
        Dados horários · Temperatura, Umidade,
        Precipitação e Vento
    </div>
    """, unsafe_allow_html=True)

    # =========================
    # FILTROS
    # =========================

    c1, c2, c3, c4 = st.columns([2,2,1,1])

    with c1:

        st.markdown(
            '<div class="filter-label">ESTAÇÃO</div>',
            unsafe_allow_html=True
        )

        station_name = st.selectbox(
            "",
            list(stations.keys())
        )

    with c2:

        st.markdown(
            '<div class="filter-label">PRODUTO</div>',
            unsafe_allow_html=True
        )

        produto = st.radio(
            "",
            [
                "Resumo Diário",
                "Eventos Extremos",
                "Ranqueamento"
            ],
            horizontal=True
        )

    with c3:

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

    with c4:

        st.markdown(
            '<div class="filter-label">DATA</div>',
            unsafe_allow_html=True
        )

        selected_date = st.date_input(
            "",
            format="DD/MM/YYYY"
        )

    # =========================
    # LOAD DATA
    # =========================

    file_name = stations[station_name]

    df = load_station_data(file_name)

    df = filter_period(df, period)

    if df.empty:

        st.warning("Sem dados disponíveis.")
        return

    # =========================
    # PRODUTOS
    # =========================

    if produto == "Resumo Diário":

        render_resumo(
            df,
            station_name,
            period
        )

    elif produto == "Eventos Extremos":

        render_extremos(df)

    elif produto == "Ranqueamento":

        render_ranking(df)


def render_resumo(df, station_name, period):

    # =========================
    # REMOVE NaN
    # =========================

    temp_max_series = df["temp_max"].dropna()
    temp_min_series = df["temp_min"].dropna()
    umi_series = df["umi_max"].dropna()
    chuva_series = df["chuva"].dropna()
    vento_series = df["vento_vel"].dropna()

    latest = df.iloc[-1]

    # =========================
    # KPIs
    # =========================

    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:

        metric_card(
            "TEMP. MÁX. HOJE",
            round(temp_max_series.iloc[-1], 1),
            "°C",
            "↑ +1.8°C vs ontem",
            "#E53935"
        )

    with k2:

        metric_card(
            "TEMP. MÍN. HOJE",
            round(temp_min_series.iloc[-1], 1),
            "°C",
            "↓ −0.5°C vs ontem",
            "#29B6F6"
        )

    with k3:

        metric_card(
            "UMIDADE MÁX.",
            round(umi_series.iloc[-1], 1),
            "%",
            "típico para abril/AM",
            "#43A047"
        )

    with k4:

        metric_card(
            "PREC. 24 H",
            round(chuva_series.iloc[-1], 1),
            "mm",
            "↑ acima da média",
            "#26C6DA"
        )

    with k5:

        metric_card(
            "VEL. VENTO",
            round(vento_series.iloc[-1], 1),
            "m/s",
            f"Raj. {latest['vento_raj']:.1f} m/s",
            "#FB8C00"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================
    # GRÁFICOS
    # =========================

    period_label = period.replace("Últimos ", "").replace(" dias", " dias")

    cidade = station_name.split(" (")[0].title()

    total_chuva = round(df["chuva"].fillna(0).sum(), 1)

    # =========================
    # DADOS DIÁRIOS
    # =========================

    df_daily = (
        df.groupby("data")
        .agg({
            "temp_max": "max",
            "temp_min": "min",
            "umi_max": "max",
            "chuva": "sum"
        })
        .reset_index()
    )

    # =========================
    # GRÁFICOS
    # =========================

    c1, c2 = st.columns(2)

    # =========================
    # TEMPERATURA
    # =========================

    with c1:

        fig_temp = go.Figure()

        # TEMP MÁX
        fig_temp.add_trace(
            go.Scatter(
                x=df_daily["data"],
                y=df_daily["temp_max"],

                mode="markers+lines",

                name="Máx. (°C)",

                line=dict(
                    color="#EF4444",
                    width=3,
                    shape="spline"
                ),

                fill=None,

                fillcolor="rgba(239,68,68,0.08)",


                marker=dict(
                    size=10,
                    color='red',
                    symbol='circle'
                )
            )
        )

        # TEMP MÍN
        fig_temp.add_trace(
            go.Scatter(
                x=df_daily["data"],
                y=df_daily["temp_min"],

                mode="markers+lines",

                name="Mín. (°C)",

                line=dict(
                    color="#22B8CF",
                    width=3,
                    shape="spline"
                ),

                fill=None,

                fillcolor="rgba(59, 130, 246, 0.08)",

                marker=dict(
                    size=10,
                    color='#22B8CF',
                    symbol='circle'
                )
            )
        )

        fig_temp.update_layout(

            title=dict(
                text="TEMPERATURA (°C)",
                x=0,

                font=dict(
                    size=15,
                    color="#374151"
                )
            ),

            height=350,

            paper_bgcolor="white",
            plot_bgcolor="white",

            hovermode="x unified",

            legend=dict(
                orientation="h",
                y=1.12,
                x=0
            ),

            annotations=[

                dict(
                    text=f"{period_label} · {cidade}",

                    x=1,
                    y=1.16,

                    xref="paper",
                    yref="paper",

                    xanchor="right",

                    showarrow=False,

                    font=dict(
                        size=11,
                        color="#C62828"
                    ),

                    bgcolor="#FDECEC",

                    bordercolor="#F5C2C2",
                    borderwidth=1,

                    borderpad=6
                )
            ],

            margin=dict(
                l=10,
                r=10,
                t=60,
                b=10
            ),

            xaxis=dict(
                showgrid=True,
                gridcolor="rgba(0,0,0,.05)"
            ),

            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(0,0,0,.05)"
            )
        )

        st.plotly_chart(
            fig_temp,
            use_container_width=True
        )

    # =========================
    # UMIDADE
    # =========================

    with c2:

        fig_umid = go.Figure()

        fig_umid.add_trace(
            go.Scatter(
                x=df_daily["data"],
                y=df_daily["umi_max"],

                mode="markers+lines",

                name="Umidade (%)",

                line=dict(
                    color="#16A34A",
                    width=3,
                    shape="spline"
                ),

                fill=None,

                fillcolor="rgba(22,163,74,0.08)",

                marker=dict(
                    size=10,
                    color="#16A34A",
                    symbol="circle"
                )
            )
        )

        fig_umid.update_layout(

            title=dict(
                text="UMIDADE MÁXIMA (%)",
                x=0,

                font=dict(
                    size=15,
                    color="#374151"
                )
            ),

            height=350,

            paper_bgcolor="white",
            plot_bgcolor="white",

            hovermode="x unified",

            legend=dict(
                orientation="h",
                y=1.12,
                x=0
            ),

            annotations=[

                dict(
                    text=f"{period_label} · {cidade}",

                    x=1,
                    y=1.16,

                    xref="paper",
                    yref="paper",

                    xanchor="right",

                    showarrow=False,

                    font=dict(
                        size=11,
                        color="#166534"
                    ),

                    bgcolor="#DCFCE7",

                    bordercolor="#86EFAC",
                    borderwidth=1,

                    borderpad=6
                )
            ],

            margin=dict(
                l=10,
                r=10,
                t=60,
                b=10
            ),

            xaxis=dict(
                showgrid=True,
                gridcolor="rgba(0,0,0,.05)"
            ),

            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(0,0,0,.05)"
            )
        )

        st.plotly_chart(
            fig_umid,
            use_container_width=True
        )

    # =========================
    # PRECIPITAÇÃO
    # =========================

    fig_prec = go.Figure()

    fig_prec.add_trace(
        go.Bar(
            x=df_daily["data"],
            y=df_daily["chuva"],

            name="Precipitação",

            marker=dict(
                color="#6EC6D1"
            )
        )
    )

    fig_prec.update_layout(

        title=dict(
            text="PRECIPITAÇÃO DIÁRIA (MM)",
            x=0,

            font=dict(
                size=15,
                color="#374151"
            )
        ),

        height=350,

        paper_bgcolor="white",
        plot_bgcolor="white",

        hovermode="x unified",

        legend=dict(
            orientation="h",
            y=1.12,
            x=0
        ),

        annotations=[

            dict(
                text=f"{period_label} · Total {total_chuva} mm",

                x=1,
                y=1.16,

                xref="paper",
                yref="paper",

                xanchor="right",

                showarrow=False,

                font=dict(
                    size=11,
                    color="#0F766E"
                ),

                bgcolor="#ECFEFF",

                bordercolor="#A5F3FC",
                borderwidth=1,

                borderpad=6
            )
        ],

        margin=dict(
            l=10,
            r=10,
            t=60,
            b=10
        ),

        xaxis=dict(
            showgrid=False
        ),

        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(0,0,0,.05)"
        )
    )

    st.plotly_chart(
        fig_prec,
        use_container_width=True
    )

def render_extremos(df):

    st.markdown("## Eventos Extremos")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Maior Temperatura",
            f"{df['temp_max'].max():.1f} °C"
        )

    with c2:
        st.metric(
            "Maior Chuva",
            f"{df['chuva'].max():.1f} mm"
        )

    with c3:
        st.metric(
            "Maior Rajada",
            f"{df['vento_raj'].max():.1f} m/s"
        )

def render_ranking(df):

    st.markdown("## Ranqueamento")

    ranking = (
        df.groupby("data")["chuva"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    st.dataframe(ranking)