import os
import pandas as pd
import streamlit as st

import plotly.graph_objects as go
from babel.dates import format_date

import plotly.graph_objects as go
import plotly.express as px

from datetime import timedelta


# =========================
# PATHS
# =========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, "datasets", "inmet")

# =========================
# MAPA DE COLUNAS
# =========================

COLUMN_MAP = {
    "Data": "data",
    "Hora (UTC)": "hora",
    "Temp. Ins. (C)": "temp_inst",
    "Temp. Max. (C)": "temp_max",
    "Temp. Min. (C)": "temp_min",
    "Umi. Ins. (%)": "umi_inst",
    "Umi. Max. (%)": "umi_max",
    "Umi. Min. (%)": "umi_min",
    "Pto Orvalho Ins. (C)": "orvalho_inst",
    "Pto Orvalho Max. (C)": "orvalho_max",
    "Pto Orvalho Min. (C)": "orvalho_min",
    "Pressao Ins. (hPa)": "pressao_inst",
    "Pressao Max. (hPa)": "pressao_max",
    "Pressao Min. (hPa)": "pressao_min",
    "Vel. Vento (m/s)": "vento_vel",
    "Dir. Vento (m/s)": "vento_dir",
    "Raj. Vento (m/s)": "vento_raj",
    "Radiacao (KJ/m²)": "radiacao",
    "Chuva (mm)": "chuva",
}

# =========================
# COLUNAS NUMÉRICAS
# =========================

NUMERIC_COLS = [
    "temp_inst",
    "temp_max",
    "temp_min",
    "umi_inst",
    "umi_max",
    "umi_min",
    "orvalho_inst",
    "orvalho_max",
    "orvalho_min",
    "pressao_inst",
    "pressao_max",
    "pressao_min",
    "vento_vel",
    "vento_raj",
    "radiacao",
    "chuva",
]

# =========================
# LOAD CSV
# =========================


@st.cache_data(show_spinner=False)
def load_station_data(station_file):

    path = os.path.join(DATASET_DIR, station_file)

    # =========================
    # ARQUIVO NÃO EXISTE
    # =========================

    if not os.path.exists(path):

        st.warning(f"Arquivo não encontrado: {station_file}")

        return pd.DataFrame()

    try:

        # =========================
        # LEITURA CSV
        # =========================

        df = pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig")

        # =========================
        # LIMPA COLUNAS
        # =========================

        df.columns = df.columns.str.strip()

        # remove colunas inúteis
        useless_cols = ["Unnamed: 0", "index"]

        existing_cols = [col for col in useless_cols if col in df.columns]

        if existing_cols:

            df.drop(columns=existing_cols, inplace=True)

        # =========================
        # RENOMEIA
        # =========================

        df.rename(columns=COLUMN_MAP, inplace=True)

        # =========================
        # DATA + HORA
        # =========================

        if "data" in df.columns and "hora" in df.columns:

            # limpa hora
            df["hora"] = (
                df["hora"].astype(str).str.replace(":", "", regex=False).str.zfill(4)
            )

            # junta data + hora
            df["datetime"] = pd.to_datetime(
                df["data"].astype(str)
                + " "
                + df["hora"].str[:2]
                + ":"
                + df["hora"].str[2:],
                errors="coerce",
            )

            # substitui data
            df["data"] = df["datetime"]

        # =========================
        # NUMÉRICOS
        # =========================

        for col in NUMERIC_COLS:

            if col in df.columns:

                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace(",", ".", regex=False)
                    .str.replace("None", "", regex=False)
                    .str.replace("--", "", regex=False)
                    .str.strip()
                )

                df[col] = pd.to_numeric(df[col], errors="coerce")

        # =========================
        # ORDENA
        # =========================

        if "data" in df.columns:

            df = df.sort_values("data")

        # =========================
        # RESET INDEX
        # =========================

        df.reset_index(drop=True, inplace=True)

        return df

    except Exception as e:

        st.error(f"Erro ao carregar {station_file}: {e}")

        return pd.DataFrame()


# =========================
# FILTRO DE PERÍODO
# =========================


def filter_period(df, period):

    if df.empty:

        return df

    if "data" not in df.columns:

        return df

    today = df["data"].max()

    # =========================
    # ÚLTIMOS 30 DIAS
    # =========================

    if period == "Últimos 30 dias":

        start = today - pd.Timedelta(days=30)

    # =========================
    # ÚLTIMOS 15 DIAS
    # =========================

    elif period == "Últimos 15 dias":

        start = today - pd.Timedelta(days=15)

    # =========================
    # ESTE MÊS
    # =========================

    elif period == "Este mês":

        start = today.replace(day=1)

    # =========================
    # SEM FILTRO
    # =========================

    else:

        return df

    return df[df["data"] >= start]


# =========================
# ESTAÇÕES
# =========================

stations = {
    "MANAUS (A101)": "MANAUS.csv",
    # "APUI (A113)": "APUI.csv",
    # "AUTAZES (A120)": "AUTAZES.csv",
    "BARCELOS (A128)": "BARCELOS.csv",
    "BOCA DO ACRE (A110)": "BOCA_DO_ACRE.csv",
    "COARI (A117)": "COARI.csv",
    # "EIRUNEPÉ (A132)": "EIRUNEPE.csv",
    "HUMAITÁ (A112)": "HUMAITA.csv",
    "ITACOATIARA (A121)": "ITACOATIARA.csv",
    # "LÁBREA (A111)": "LABREA.csv",
    "MANACAPURU (A119)": "MANACAPURU.csv",
    "MANICORÉ (A133)": "MANICORE.csv",
    # "MAUES (A122)": "MAUES.csv",
    "NOVO ARIPUANÃ (A144)": "NOVO_ARIPUANÃ.csv",
    "PARINTINS (A123)": "PARINTINS.csv",
    "SÃO GABRIEL DA CACHOEIRA (A134)": "SGCACHOEIRA.csv",
    "URUCARÁ (A124)": "URUCARÁ.csv",
}

# =========================
# CARD KPI
# =========================


def metric_card(title, value, unit, extra, color):

    st.markdown(
        f"""
        <div style="
            background:white;
            border: 2px solid {color};
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
                line-height:1;
                color:{color};
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
        unsafe_allow_html=True,
    )


# =========================
# RENDER
# =========================


def render():

    # =====================================================
    # TÍTULO
    # =====================================================

    st.markdown(
        """
    <div class="main-title">
        Estações INMET
    </div>

    <div class="subtitle">
        Dados horários · Temperatura, Umidade,
        Precipitação e Vento
    </div>
    """,
        unsafe_allow_html=True,
    )

    # =====================================================
    # FILTROS
    # =====================================================

    c1, c2, c3, c4 = st.columns(
        [2.0, 1.6, 1.0, 1.0],
        gap="small"
    )

    # =====================================================
    # PRODUTO
    # =====================================================

    with c1:

        st.markdown(
            '<div class="filter-label">PRODUTO</div>',
            unsafe_allow_html=True
        )

        produto = st.radio(
            "",
            [
                "Resumo Diário",
                "Eventos Extremos",
                "Registro Diário"
            ],
            horizontal=True,
            label_visibility="collapsed",
        )

    # =====================================================
    # ESTAÇÃO
    # =====================================================

    with c2:

        st.markdown(
            '<div class="filter-label">ESTAÇÃO</div>',
            unsafe_allow_html=True
        )

        if produto == "Eventos Extremos":

            station_options = [
                "Todas as estações",
                *stations.keys()
            ]

        else:

            station_options = list(stations.keys())

        station_name = st.selectbox(
            "",
            station_options,
            label_visibility="collapsed"
        )

    # =====================================================
    # CARREGA DADOS
    # =====================================================

    if station_name == "Todas as estações":

        df = pd.DataFrame()

    else:

        file_name = stations[station_name]

        df = load_station_data(file_name)

        if df.empty:

            st.warning("Nenhum dado encontrado para esta estação.")
            return

    # =====================================================
    # INTERVALO DISPONÍVEL
    # =====================================================

    if station_name == "Todas as estações":

        datas = []

        for arquivo in stations.values():

            if arquivo is None:
                continue

            d = load_station_data(arquivo)

            if d.empty:
                continue

            datas.append(d["data"])

        if not datas:

            st.warning("Nenhum dado encontrado.")
            return

        serie_datas = pd.concat(datas)

    else:

        serie_datas = df["data"]

    min_date = serie_datas.min().date()
    max_date = serie_datas.max().date()

    if pd.isna(min_date) or pd.isna(max_date):

        st.warning("Dados de data inválidos.")
        return

    selected_date = None
    start_date = None
    end_date = None

    # =====================================================
    # FILTROS DE DATA
    # =====================================================

    if produto == "Registro Diário":

        with c3:

            st.markdown(
                '<div class="filter-label">DATA</div>',
                unsafe_allow_html=True
            )

            selected_date = st.date_input(
                "",
                value=max_date,
                min_value=min_date,
                max_value=max_date,
                format="DD/MM/YYYY",
                label_visibility="collapsed",
            )

    else:

        default_start = max(
            min_date,
            max_date - timedelta(days=14)
        )

        with c3:

            st.markdown(
                '<div class="filter-label">DATA INÍCIO</div>',
                unsafe_allow_html=True
            )

            start_date = st.date_input(
                "",
                value=default_start,
                min_value=min_date,
                max_value=max_date,
                key="periodo_inicio",
                format="DD/MM/YYYY",
                label_visibility="collapsed",
            )

        with c4:

            st.markdown(
                '<div class="filter-label">DATA FIM</div>',
                unsafe_allow_html=True
            )

            end_date = st.date_input(
                "",
                value=max_date,
                min_value=min_date,
                max_value=max_date,
                key="periodo_fim",
                format="DD/MM/YYYY",
                label_visibility="collapsed",
            )

    # =====================================================
    # FILTRA DATA
    # =====================================================

    if (
        produto != "Registro Diário"
        and station_name != "Todas as estações"
        and start_date
        and end_date
    ):

        df = df[(df["data"].dt.date >= start_date) & (df["data"].dt.date <= end_date)]

    # =====================================================
    # RENDERIZA
    # =====================================================

    if produto == "Resumo Diário":

        render_resumo(df, station_name, start_date, end_date, produto)

    elif produto == "Eventos Extremos":

        render_extremos(
            df=df,
            station=station_name,
            data_inicio=start_date,
            data_fim=end_date,
        )

    else:

        render_registro_diario(df, selected_date, station_name)


# =========================
# TICKS PT-BR
# =========================


def build_month_ticks(df, col="data"):

    tickvals = pd.date_range(df[col].min(), df[col].max(), freq="MS")

    meses_pt = {
        1: "Jan",
        2: "Fev",
        3: "Mar",
        4: "Abr",
        5: "Mai",
        6: "Jun",
        7: "Jul",
        8: "Ago",
        9: "Set",
        10: "Out",
        11: "Nov",
        12: "Dez",
    }

    ticktext = [f"{meses_pt[d.month]}/{d.year}" for d in tickvals]

    return tickvals, ticktext


def build_daily_ticks(df, col="data"):

    tickvals = pd.date_range(
        df[col].min().normalize(),
        df[col].max().normalize(),
        freq="D"
    )

    ticktext = [
        d.strftime("%d/%m")
        for d in tickvals
    ]

    return tickvals, ticktext


def build_hourly_ticks(df, col="data", intervalo="1H"):

    tickvals = pd.date_range(
        df[col].min(),
        df[col].max(),
        freq=intervalo
    )

    ticktext = [
        d.strftime("%H:%M")
        for d in tickvals
    ]

    return tickvals, ticktext
# =========================
# PROCESSA ROSA DOS VENTOS
# =========================


def process_wind_rose(df):

    # =========================
    # CONVERTE GRAUS -> DIREÇÃO
    # =========================

    def grau_para_direcao(grau):

        if pd.isna(grau):
            return None

        grau = float(grau)

        setores = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]

        indice = int((grau + 22.5) // 45) % 8

        return setores[indice]

    # =========================
    # DIREÇÃO CONVERTIDA
    # =========================

    df = df.copy()

    df["dir_cardinal"] = df["vento_dir"].apply(grau_para_direcao)

    direcoes = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]

    freq = []
    vel_media = []

    for d in direcoes:

        subset = df[df["dir_cardinal"] == d]

        freq.append(len(subset))

        vel = subset["vento_vel"].mean()

        vel_media.append(0 if pd.isna(vel) else round(vel, 1))

    return direcoes, freq, vel_media


def render_resumo(df, station_name, start_date, end_date, produto):

    # =========================
    # REMOVE NaN
    # =========================

    temp_max_series = df["temp_max"].dropna()
    temp_min_series = df["temp_min"].dropna()
    umi_series = df["umi_max"].dropna()
    chuva_series = df["chuva"].dropna()
    vento_series = df["vento_vel"].dropna()

    latest = df.iloc[-1]

    if temp_max_series.empty:
        return

    if df.empty:

        st.warning("Sem dados disponíveis.")
        return

    # =========================
    # KPIs
    # =========================

    # =====================================================
    # DEFINIR MODO DE COMPARAÇÃO
    # =====================================================

    modo = "resumo"

    # =====================================================
    # FUNÇÃO AUXILIAR
    # =====================================================

    def obter_valores(serie, modo):

        atual = serie.iloc[-1]

        # ===============================================
        # RESUMO DIÁRIO
        # compara:
        # data fim vs data início
        # ===============================================

        if modo == "resumo":

            referencia = serie.iloc[0]
            texto_ref = "vs data inicial"

        # ===============================================
        # REGISTRO DIÁRIO
        # compara:
        # dia atual vs dia anterior
        # ===============================================

        else:

            referencia = serie.iloc[-2]
            texto_ref = "vs dia anterior"

        diff = atual - referencia

        return atual, diff, texto_ref

    # =====================================================
    # FUNÇÃO FORMATAR
    # =====================================================

    def format_diff(valor, texto_ref, unidade=""):

        if valor > 0:

            seta = "↑"

        elif valor < 0:

            seta = "↓"

        else:

            seta = "•"

        return f"{seta} " f"{valor:+.1f}{unidade} " f"{texto_ref}"

    # =====================================================
    # CÁLCULOS
    # =====================================================

    temp_max_hoje, diff_temp_max, txt_ref = obter_valores(temp_max_series, modo)

    temp_min_hoje, diff_temp_min, _ = obter_valores(temp_min_series, modo)

    umi_hoje, diff_umi, _ = obter_valores(umi_series, modo)

    chuva_hoje, diff_chuva, _ = obter_valores(chuva_series, modo)

    # =====================================================
    # VENTO
    # usa velocidade máxima
    # =====================================================

    vento_hoje = vento_series.max()

    if modo == "resumo":

        vento_ref = vento_series.iloc[0]
        txt_vento = "vs data inicial"

    else:

        vento_ref = vento_series.iloc[-2]
        txt_vento = "vs dia anterior"

    diff_vento = vento_hoje - vento_ref

    # =====================================================
    # CARDS
    # =====================================================

    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:

        metric_card(
            "TEMP. MÁX. HOJE",
            round(temp_max_hoje, 1),
            "°C",
            format_diff(diff_temp_max, txt_ref, "°C"),
            "#E53935",
        )

    with k2:

        metric_card(
            "TEMP. MÍN. HOJE",
            round(temp_min_hoje, 1),
            "°C",
            format_diff(diff_temp_min, txt_ref, "°C"),
            "#29B6F6",
        )

    with k3:

        metric_card(
            "UMIDADE MÁX.",
            round(umi_hoje, 1),
            "%",
            format_diff(diff_umi, txt_ref, "%"),
            "#43A047",
        )

    with k4:

        metric_card(
            "PREC. 24 H",
            round(chuva_hoje, 1),
            "mm",
            format_diff(diff_chuva, txt_ref, " mm"),
            "#26C6DA",
        )

    with k5:

        metric_card(
            "VEL. VENTO MÁX.",
            round(vento_hoje, 1),
            "m/s",
            format_diff(diff_vento, txt_vento, " m/s"),
            "#FB8C00",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================
    # GRÁFICOS
    # =========================

    period_label = (
        f"{format_date(start_date, format='dd/MMM/yyyy', locale='pt_BR')}"
        f" → "
        f"{format_date(end_date, format='dd/MMM/yyyy', locale='pt_BR')}"
    )

    cidade = station_name.split(" (")[0].title()

    total_chuva = round(df["chuva"].fillna(0).sum(), 1)

    # =========================
    # DADOS DIÁRIOS
    # =========================

    df_daily = (
        df.set_index("data")
        .resample("1D")
        .agg({"temp_max": "max", "temp_min": "min", "umi_max": "max", "chuva": "sum"})
        .reset_index()
    )

    tickvals, ticktext = build_daily_ticks(df_daily)

    def ptbr_xaxis(tickvals, ticktext):

        return dict(
            tickmode="array",
            tickvals=tickvals,
            ticktext=ticktext,

            title=dict(
                text="<b>Data</b>",
                font=dict(size=13)
            ),

            tickfont=dict(size=11),

            tickangle=0,

            showgrid=True,
            gridcolor="rgba(0,0,0,.05)"
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
                line=dict(color="#EF4444", width=3, shape="linear"),
                fill=None,
                fillcolor="rgba(239,68,68,0.08)",
                marker=dict(size=10, color="red", symbol="circle"),
            )
        )

        # TEMP MÍN
        fig_temp.add_trace(
            go.Scatter(
                x=df_daily["data"],
                y=df_daily["temp_min"],
                mode="markers+lines",
                name="Mín. (°C)",
                line=dict(color="#22B8CF", width=3, shape="linear"),
                fill=None,
                fillcolor="rgba(59, 130, 246, 0.08)",
                marker=dict(size=10, color="#22B8CF", symbol="circle"),
            )
        )

        fig_temp.update_layout(
            title=dict(
                text="<b>TEMPERATURA (°C)</b>",
                x=0,
                font=dict(size=15, color="#374151")
            ),
            height=350,
            paper_bgcolor="white",
            plot_bgcolor="white",
            hovermode="x unified",
            legend=dict(orientation="h", y=1.12, x=0),
            annotations=[
                dict(
                    text=(f"{period_label} · " f"{cidade}"),
                    x=1,
                    y=1.16,
                    xref="paper",
                    yref="paper",
                    xanchor="right",
                    showarrow=False,
                    font=dict(size=11, color="#C62828"),
                    bgcolor="#FDECEC",
                    bordercolor="#F5C2C2",
                    borderwidth=1,
                    borderpad=6,
                )
            ],
            margin=dict(l=10, r=10, t=60, b=10),
            # =========================
            # EIXO X
            # =========================

            xaxis=ptbr_xaxis(tickvals, ticktext),

            yaxis=dict(
                title=dict(
                    text="<b>°C</b>",
                    font=dict(size=12, color="#374151")
                ),
                showgrid=True,
                gridcolor="rgba(0,0,0,.05)",
                tickfont=dict(
                    size=11,
                    color="#374151"
                )
            ),

            )

        st.plotly_chart(fig_temp, use_container_width=True)

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
                line=dict(color="#16A34A", width=3, shape="linear"),
                fill=None,
                fillcolor="rgba(22,163,74,0.08)",
                marker=dict(size=10, color="#16A34A", symbol="circle"),
            )
        )

        fig_umid.update_layout(
            title=dict(
                text="<b>UMIDADE MÁXIMA (%)</b>", x=0, font=dict(size=15, color="#374151")
            ),
            height=350,
            paper_bgcolor="white",
            plot_bgcolor="white",
            hovermode="x unified",
            legend=dict(orientation="h", y=1.12, x=0),
            annotations=[
                dict(
                    text=(f"{period_label} · " f"{cidade}"),
                    x=1,
                    y=1.16,
                    xref="paper",
                    yref="paper",
                    xanchor="right",
                    showarrow=False,
                    font=dict(size=11, color="#166534"),
                    bgcolor="#DCFCE7",
                    bordercolor="#86EFAC",
                    borderwidth=1,
                    borderpad=6,
                )
            ],
            margin=dict(l=10, r=10, t=60, b=10),
            # =========================
            # EIXO X
            # =========================
            xaxis=ptbr_xaxis(tickvals, ticktext),
            yaxis=dict(
                title=dict(
                    text="<b>%</b>",
                    font=dict(size=12, color="#374151")
                ),
                showgrid=True,
                gridcolor="rgba(0,0,0,.05)",
                tickfont=dict(
                    size=11,
                    color="#374151"
                )
            ),

            )

        st.plotly_chart(fig_umid, use_container_width=True, config={"locale": "pt-BR"})

    # =========================
    # PRECIPITAÇÃO + ROSA DOS VENTOS
    # =========================

    c3, c4 = st.columns(2)

    # =========================
    # PRECIPITAÇÃO
    # =========================

    with c3:

        fig_prec = go.Figure()

        fig_prec.add_trace(
            go.Bar(
                x=df_daily["data"],
                y=df_daily["chuva"],
                name="Precipitação",
                marker=dict(color="#6EC6D1"),
                hovertemplate="<b>%{x}</b><br>" + "Chuva: %{y:.1f} mm<extra></extra>",
            )
        )

        fig_prec.update_layout(
            title=dict(
                text="<b>PRECIPITAÇÃO DIÁRIA (MM)</b>",
                x=0,
                font=dict(size=15, color="#374151"),
            ),
            height=350,
            paper_bgcolor="white",
            plot_bgcolor="white",
            hovermode="x unified",
            legend=dict(orientation="h", y=1.12, x=0),
            annotations=[
                dict(
                    text=(f"{period_label} · " f"Total {total_chuva:.1f} mm · " f"{cidade}"),
                    x=1,
                    y=1.16,
                    xref="paper",
                    yref="paper",
                    xanchor="right",
                    showarrow=False,
                    font=dict(size=11, color="#0F766E"),
                    bgcolor="#ECFEFF",
                    bordercolor="#A5F3FC",
                    borderwidth=1,
                    borderpad=6,
                )
            ],
            margin=dict(l=10, r=10, t=60, b=10),
            xaxis=ptbr_xaxis(tickvals, ticktext),
            yaxis=dict(
                title=dict(
                    text="<b>mm</b>",
                    font=dict(size=12, color="#374151")
                ),
                showgrid=True,
                gridcolor="rgba(0,0,0,.05)",
                tickfont=dict(
                    size=11,
                    color="#374151"
                )
            ),
        )

        st.plotly_chart(fig_prec, use_container_width=True, config={"locale": "pt-BR"})

    # =========================
    # ROSA DOS VENTOS
    # =========================

    with c4:

        direcoes, freq, vel_media = process_wind_rose(df)

        fig_vento = go.Figure()

        fig_vento.add_trace(
            go.Barpolar(
                r=freq,
                theta=direcoes,
                marker=dict(
                    color=vel_media,
                    colorscale=[
                        [0.0, "#F6F5C9"],
                        [0.2, "#DDECB2"],
                        [0.4, "#9ED9C3"],
                        [0.6, "#5CB7D6"],
                        [0.8, "#2F6DB3"],
                        [1.0, "#1B1F6B"],
                    ],
                    colorbar=dict(title="m/s"),
                    line=dict(color="white", width=1.5),
                ),
                opacity=0.95,
                hovertemplate="<b>%{theta}</b><br>"
                + "Frequência: %{r}<br>"
                + "Vel. Média: %{marker.color:.1f} m/s"
                + "<extra></extra>",
            )
        )

        fig_vento.update_layout(
            title=dict(
                text="<b>ROSA DOS VENTOS</b>", x=0, font=dict(size=15, color="#374151")
            ),
            height=350,
            paper_bgcolor="white",
            plot_bgcolor="white",
            polar=dict(
                bgcolor="white",
                radialaxis=dict(
                    showticklabels=True, ticks="", gridcolor="rgba(0,0,0,.08)"
                ),
                angularaxis=dict(direction="clockwise", rotation=90),
            ),
            margin=dict(l=10, r=10, t=60, b=10),
            showlegend=False,
        )

        st.plotly_chart(fig_vento, use_container_width=True, config={"locale": "pt-BR"})


def render_extremos(df, station, data_inicio, data_fim):

    st.markdown("## Eventos Extremos")

    # =====================================================
    # FILTROS DO PAINEL
    # =====================================================

    c1, c2, c3, c4 = st.columns([2.2, 1.1, 1.1, 1])

    with c1:

        variavel = st.selectbox(
            "Variável",
            [
                "Maior Temperatura Máxima",
                "Menor Temperatura Mínima",
                "Maior Chuva",
                "Maior Rajada",
            ],
        )

    # ------------------------------------

    anos = set()

    if station == "Todas as estações":

        arquivos = stations.values()

    else:

        arquivos = [stations[station]]

    for arquivo in arquivos:

        d = load_station_data(arquivo)

        if d.empty:
            continue

        anos.update(d["data"].dt.year.dropna().unique())

    anos = sorted(anos)

    with c2:

        ano = st.selectbox("Ano", ["Todos"] + anos)

    with c3:

        meses = [
            "Todos",
            "Janeiro",
            "Fevereiro",
            "Março",
            "Abril",
            "Maio",
            "Junho",
            "Julho",
            "Agosto",
            "Setembro",
            "Outubro",
            "Novembro",
            "Dezembro",
        ]

        mes = st.selectbox("Mês", meses)

    with c4:

        crescente = st.toggle("Ordem crescente", value=False)

    # =====================================================
    # REGRAS DAS VARIÁVEIS
    # =====================================================

    regras = {
        "Maior Temperatura Máxima": {"coluna": "temp_max", "operacao": "max"},
        "Menor Temperatura Mínima": {"coluna": "temp_min", "operacao": "min"},
        "Maior Chuva": {"coluna": "chuva", "operacao": "sum"},
        "Maior Rajada": {"coluna": "vento_raj", "operacao": "max"},
    }

    cfg = regras[variavel]

    coluna = cfg["coluna"]
    operacao = cfg["operacao"]

    registros = []

    # =====================================================
    # ESTAÇÕES
    # =====================================================

    if station == "Todas as estações":

        lista_estacoes = list(stations.items())

    else:

        lista_estacoes = [(station, stations[station])]

    for nome_estacao, arquivo in lista_estacoes:

        if station == "Todas as estações":

            df_est = load_station_data(arquivo)

        else:

            df_est = df.copy()

        if df_est.empty:
            continue

        if ano != "Todos":

            df_est = df_est[df_est["data"].dt.year == ano]

        if mes != "Todos":

            numero_mes = meses.index(mes)

            df_est = df_est[df_est["data"].dt.month == numero_mes]

        if data_inicio is not None:

            df_est = df_est[df_est["data"] >= pd.Timestamp(data_inicio)]

        if data_fim is not None:

            df_est = df_est[df_est["data"] <= pd.Timestamp(data_fim)]

        df_est = df_est.dropna(subset=[coluna])

        if df_est.empty:
            continue

        df_eventos = (
            df_est.groupby(df_est["data"].dt.normalize())
            .agg({coluna: operacao})
            .reset_index()
            .rename(columns={"data": "Data"})
        )

        if variavel == "Maior Chuva":

            df_eventos = df_eventos[df_eventos[coluna] >= 15]

        elif variavel == "Maior Rajada":

            df_eventos = df_eventos[df_eventos[coluna] > 0]

        elif variavel == "Maior Temperatura Máxima":

            df_eventos = df_eventos[df_eventos[coluna] > 0]

        elif variavel == "Menor Temperatura Mínima":

            df_eventos = df_eventos[df_eventos[coluna] > -20]

        if df_eventos.empty:
            continue

        df_eventos["Estação"] = nome_estacao

        df_eventos.rename(columns={coluna: "Valor"}, inplace=True)

        registros.append(df_eventos[["Estação", "Valor", "Data"]])
    # =====================================================
    
    if not registros:

        st.info(
            "Nenhum evento encontrado para os filtros selecionados."
        )

        return

    tabela = pd.concat(registros, ignore_index=True)

    if tabela.empty:

        st.info("Nenhum registro encontrado.")

        return

    # =====================================================
    # ORDENAÇÃO
    # =====================================================

    asc = crescente

    if variavel == "Maior Temperatura Máxima":

        asc = crescente

    elif variavel == "Menor Temperatura Mínima":

        asc = not crescente

    elif variavel == "Maior Chuva":

        asc = crescente

    elif variavel == "Maior Rajada":

        asc = crescente
    tabela = tabela.sort_values("Valor", ascending=asc).reset_index(drop=True)

    # =====================================================
    # TABELA
    # =====================================================

    tabela_exibicao = tabela.copy()

    tabela_exibicao["Data"] = tabela_exibicao["Data"].dt.strftime("%d/%m/%Y")

    if variavel == "Maior Chuva":

        tabela_exibicao["Valor"] = tabela_exibicao["Valor"].map(lambda x: f"{x:.1f} mm")

    elif variavel == "Maior Rajada":

        tabela_exibicao["Valor"] = tabela_exibicao["Valor"].map(
            lambda x: f"{x:.1f} m/s"
        )

    else:

        tabela_exibicao["Valor"] = tabela_exibicao["Valor"].map(lambda x: f"{x:.1f} °C")

    import plotly.graph_objects as go

    # ===========================================
    # TABELA DE EVENTOS
    # ===========================================

    tabela_plot = tabela_exibicao.copy()

    tabela_plot.insert(
        0,
        "Rank",
        range(1, len(tabela_plot) + 1)
    )

    st.dataframe(
        tabela_plot,
        use_container_width=True,
        height=650,
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn(
                width="small"
            ),
            "Estação": st.column_config.TextColumn(
                width=180
            ),
            "Valor": st.column_config.TextColumn(
                width=90
            ),
            "Data": st.column_config.TextColumn(
                width=100
            ),
        }
    )

    # =====================================================
    # TOP 30 PARA O GRÁFICO
    # =====================================================

    grafico = tabela.head(30).copy()

    # -----------------------------------------------------
    # Rótulo único por barra (Estação + Data)
    # Evita que o Plotly empilhe todos os registros na
    # mesma categoria do eixo Y quando há uma só estação
    # -----------------------------------------------------

    grafico["Rótulo"] = (
        grafico["Estação"] + " · " + grafico["Data"].dt.strftime("%d/%m/%Y")
    )

    fig = px.bar(
        grafico,
        x="Valor",
        y="Rótulo",
        orientation="h",
        text="Valor",
        color="Valor",
        hover_data=["Estação", "Data"],
    )

    fig.update_layout(
        title=f"Ranking - {variavel}",
        xaxis_title="Valor",
        yaxis_title="",
        height=max(600, len(grafico) * 30),
        coloraxis_showscale=False,
        yaxis=dict(autorange="reversed"),
    )

    fig.update_traces(textposition="outside")

    st.plotly_chart(fig, use_container_width=True)


def render_registro_diario(df, selected_date, station_name):

    st.markdown("## Registro Diário")

    # =========================
    # FILTRA DATA
    # =========================

    df_day = df[df["data"].dt.date == selected_date]
    # st.write(df_day["vento_dir"].unique())

    df_day = df_day.copy()

    df_day["hora_formatada"] = pd.to_datetime(
        df_day["hora"].astype(str).str.zfill(4), format="%H%M"
    )

    if df_day.empty:

        st.warning("Sem registros para esta data.")
        return

    # =========================
    # DADOS
    # =========================

    temp_max = df_day["temp_max"].max()
    temp_min = df_day["temp_min"].min()

    umi_max = df_day["umi_max"].max()

    chuva_total = df_day["chuva"].sum()

    vento_max = df_day["vento_vel"].max()

    # =========================
    # DIA ANTERIOR
    # =========================

    previous_date = (pd.to_datetime(selected_date) - pd.Timedelta(days=1)).date()

    df_prev = df[df["data"].dt.date == previous_date]

    # =========================
    # VALORES DIA ANTERIOR
    # =========================

    if not df_prev.empty:

        temp_max_prev = df_prev["temp_max"].max()
        temp_min_prev = df_prev["temp_min"].min()

        umi_prev = df_prev["umi_max"].max()

        chuva_prev = df_prev["chuva"].sum()

        vento_prev = df_prev["vento_vel"].max()

    else:

        temp_max_prev = temp_max
        temp_min_prev = temp_min

        umi_prev = umi_max

        chuva_prev = chuva_total

        vento_prev = vento_max

    # =========================
    # DIFERENÇAS
    # =========================

    diff_temp_max = temp_max - temp_max_prev
    diff_temp_min = temp_min - temp_min_prev

    diff_umi = umi_max - umi_prev

    diff_chuva = chuva_total - chuva_prev

    diff_vento = vento_max - vento_prev

    # =========================
    # FORMATADOR
    # =========================

    def format_diff(valor, unidade=""):

        if valor > 0:

            seta = "↑"

        elif valor < 0:

            seta = "↓"

        else:

            seta = "•"

        return f"{seta} " f"{valor:+.1f}{unidade} " f"vs dia anterior"

    # =========================
    # KPIs
    # =========================

    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:

        metric_card(
            "TEMP. MÁX.",
            round(temp_max, 1),
            "°C",
            format_diff(diff_temp_max, "°C"),
            "#E53935",
        )

    with k2:

        metric_card(
            "TEMP. MÍN.",
            round(temp_min, 1),
            "°C",
            format_diff(diff_temp_min, "°C"),
            "#29B6F6",
        )

    with k3:

        metric_card(
            "UMIDADE MÁX.",
            round(umi_max, 1),
            "%",
            format_diff(diff_umi, "%"),
            "#43A047",
        )

    with k4:

        metric_card(
            "PRECIPITAÇÃO",
            round(chuva_total, 1),
            "mm",
            format_diff(diff_chuva, "mm"),
            "#26C6DA",
        )

    with k5:

        metric_card(
            "VENTO MÁX.",
            round(vento_max, 1),
            "m/s",
            format_diff(diff_vento, "m/s"),
            "#FB8C00",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================
    # GRÁFICOS
    # =========================

    c1, c2 = st.columns(2)

    # =========================
    # TEMPERATURA
    # =========================

    with c1:

        fig_temp = go.Figure()

        fig_temp.add_trace(
            go.Scatter(
                x=df_day["hora_formatada"],
                y=df_day["temp_max"],
                mode="markers+lines",
                name="Temp. Máx.",
                line=dict(color="#EF4444", width=3, shape="linear"),
            )
        )

        fig_temp.add_trace(
            go.Scatter(
                x=df_day["hora_formatada"],
                y=df_day["temp_min"],
                mode="markers+lines",
                name="Temp. Mín.",
                line=dict(color="#22B8CF", width=3, shape="linear"),
            )
        )

        fig_temp.update_layout(
            title=dict(
                text="TEMPERATURA HORÁRIA (°C)",
                x=0,
                font=dict(size=15, color="#374151"),
            ),
            height=350,
            paper_bgcolor="white",
            plot_bgcolor="white",
            hovermode="x unified",
            legend=dict(orientation="h", y=1.12, x=0),
            annotations=[
                dict(
                    text=(
                        f"{station_name.split(' (')[0].title()} · "
                        f"{format_date(selected_date, format='dd/MM/yyyy', locale='pt_BR')}"
                    ),
                    x=1,
                    y=1.16,
                    xref="paper",
                    yref="paper",
                    xanchor="right",
                    showarrow=False,
                    font=dict(size=11, color="#C62828"),
                    bgcolor="#FDECEC",
                    bordercolor="#F5C2C2",
                    borderwidth=1,
                    borderpad=6,
                )
            ],
            margin=dict(l=10, r=10, t=60, b=10),
            xaxis=dict(
                dtick=21600000,
                tickformat="%H:%M",
                showgrid=True,
                gridcolor="rgba(0,0,0,.05)",
            ),
            yaxis=dict(
                title=dict(
                    text="<b>°C</b>",
                    font=dict(size=12, color="#374151")
                ),
                showgrid=True,
                gridcolor="rgba(0,0,0,.05)",
                tickfont=dict(
                    size=11,
                    color="#374151"
                )
            ),
        )

        st.plotly_chart(fig_temp, use_container_width=True, config={"locale": "pt-BR"})

    # =========================
    # UMIDADE
    # =========================

    with c2:

        fig_umid = go.Figure()

        fig_umid.add_trace(
            go.Scatter(
                x=df_day["hora_formatada"],
                y=df_day["umi_max"],
                mode="markers+lines",
                name="Umidade",
                line=dict(color="#16A34A", width=3, shape="linear"),
                fill="tozeroy",
                fillcolor="rgba(22,163,74,.08)",
            )
        )

        y_min = max(0, df_day["umi_max"].min() - 10)

        y_max = min(100, df_day["umi_max"].max() + 5)

        fig_umid.update_layout(
            title=dict(
                text="UMIDADE HORÁRIA (%)", x=0, font=dict(size=15, color="#374151")
            ),
            height=350,
            paper_bgcolor="white",
            plot_bgcolor="white",
            hovermode="x unified",
            legend=dict(orientation="h", y=1.12, x=0),
            annotations=[
                dict(
                    text=(
                        f"{station_name.split(' (')[0].title()} · "
                        f"{format_date(selected_date, format='dd/MM/yyyy', locale='pt_BR')}"
                    ),
                    x=1,
                    y=1.16,
                    xref="paper",
                    yref="paper",
                    xanchor="right",
                    showarrow=False,
                    font=dict(size=11, color="#166534"),
                    bgcolor="#DCFCE7",
                    bordercolor="#86EFAC",
                    borderwidth=1,
                    borderpad=6,
                )
            ],
            margin=dict(l=10, r=10, t=60, b=10),
            xaxis=dict(
                dtick=21600000,
                tickformat="%H:%M",
                showgrid=True,
                gridcolor="rgba(0,0,0,.05)",
            ),
            yaxis=dict(
                title=dict(
                    text="<b>%</b>",
                    font=dict(size=12, color="#374151")
                ),
                range=[y_min, y_max],
                showgrid=True,
                gridcolor="rgba(0,0,0,.05)",
                tickfont=dict(
                    size=11,
                    color="#374151"
                )
            ),
        )

        st.plotly_chart(fig_umid, use_container_width=True, config={"locale": "pt-BR"})

    # =========================
    # PRECIPITAÇÃO + ROSA
    # =========================

    c3, c4 = st.columns(2)

    # PRECIPITAÇÃO
    with c3:

        fig_prec = go.Figure()

        fig_prec.add_trace(
            go.Bar(
                x=df_day["hora_formatada"],
                y=df_day["chuva"],
                marker=dict(color="#6EC6D1"),
            )
        )

        fig_prec.update_layout(
            title=dict(
                text="PRECIPITAÇÃO HORÁRIA (MM)",
                x=0,
                font=dict(size=15, color="#374151"),
            ),
            height=350,
            paper_bgcolor="white",
            plot_bgcolor="white",
            hovermode="x unified",
            margin=dict(l=10, r=10, t=60, b=10),
            annotations=[
                dict(
                    text=f"Total diário · {round(chuva_total,1)} mm",
                    x=1,
                    y=1.16,
                    xref="paper",
                    yref="paper",
                    xanchor="right",
                    showarrow=False,
                    font=dict(size=11, color="#0F766E"),
                    bgcolor="#ECFEFF",
                    bordercolor="#A5F3FC",
                    borderwidth=1,
                    borderpad=6,
                )
            ],
            xaxis=dict(dtick=21600000, tickformat="%H:%M", showgrid=False),
            yaxis=dict(
                title=dict(
                    text="<b>mm</b>",
                    font=dict(size=12, color="#374151")
                ),
                range=[y_min, y_max],
                showgrid=True,
                gridcolor="rgba(0,0,0,.05)",
                tickfont=dict(
                    size=11,
                    color="#374151"
                )
            ),
        )
        st.plotly_chart(fig_prec, use_container_width=True, config={"locale": "pt-BR"})

    # ROSA DOS VENTOS
    with c4:

        direcoes, freq, vel_media = process_wind_rose(df_day)

        fig_vento = go.Figure()

        fig_vento.add_trace(
            go.Barpolar(
                r=freq,
                theta=direcoes,
                marker=dict(
                    color=vel_media,
                    colorscale=[
                        [0.0, "#F6F5C9"],
                        [0.2, "#DDECB2"],
                        [0.4, "#9ED9C3"],
                        [0.6, "#5CB7D6"],
                        [0.8, "#2F6DB3"],
                        [1.0, "#1B1F6B"],
                    ],
                    colorbar=dict(title="m/s"),
                    line=dict(color="white", width=1.5),
                ),
                hovertemplate="<b>%{theta}</b><br>"
                + "Frequência: %{r}<br>"
                + "Vel. Média: %{marker.color:.1f} m/s"
                + "<extra></extra>",
            )
        )

        fig_vento.update_layout(
            title=dict(
                text="ROSA DOS VENTOS", x=0, font=dict(size=15, color="#374151")
            ),
            height=350,
            paper_bgcolor="white",
            plot_bgcolor="white",
            polar=dict(
                bgcolor="white",
                radialaxis=dict(
                    showticklabels=True, ticks="", gridcolor="rgba(0,0,0,.08)"
                ),
                angularaxis=dict(direction="clockwise", rotation=90),
            ),
            margin=dict(l=10, r=10, t=60, b=10),
            showlegend=False,
        )

        st.plotly_chart(fig_vento, use_container_width=True, config={"locale": "pt-BR"})
