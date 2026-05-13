import os
import pandas as pd
import streamlit as st

# =========================
# PATHS
# =========================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATASET_DIR = os.path.join(
    BASE_DIR,
    "datasets",
    "inmet"
)

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

    "Chuva (mm)": "chuva"
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
    "chuva"
]

# =========================
# LOAD CSV
# =========================

@st.cache_data(show_spinner=False)
def load_station_data(station_file):

    path = os.path.join(
        DATASET_DIR,
        station_file
    )

    # =========================
    # ARQUIVO NÃO EXISTE
    # =========================

    if not os.path.exists(path):

        st.warning(
            f"Arquivo não encontrado: {station_file}"
        )

        return pd.DataFrame()

    try:

        # =========================
        # LEITURA CSV
        # =========================

        df = pd.read_csv(
            path,
            sep=None,
            engine="python",
            encoding="utf-8-sig"
        )

        # =========================
        # LIMPA COLUNAS
        # =========================

        df.columns = (
            df.columns
            .str.strip()
        )

        # remove colunas inúteis
        useless_cols = [
            "Unnamed: 0",
            "index"
        ]

        existing_cols = [
            col for col in useless_cols
            if col in df.columns
        ]

        if existing_cols:

            df.drop(
                columns=existing_cols,
                inplace=True
            )

        # =========================
        # RENOMEIA
        # =========================

        df.rename(
            columns=COLUMN_MAP,
            inplace=True
        )

        # =========================
        # DATA + HORA
        # =========================

        if "data" in df.columns and "hora" in df.columns:

            # limpa hora
            df["hora"] = (
                df["hora"]
                .astype(str)
                .str.replace(":", "", regex=False)
                .str.zfill(4)
            )

            # junta data + hora
            df["datetime"] = pd.to_datetime(
                df["data"].astype(str) + " " +
                df["hora"].str[:2] + ":" +
                df["hora"].str[2:],
                errors="coerce"
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

                    .str.replace(
                        ",",
                        ".",
                        regex=False
                    )

                    .str.replace(
                        "None",
                        "",
                        regex=False
                    )

                    .str.replace(
                        "--",
                        "",
                        regex=False
                    )

                    .str.strip()
                )

                df[col] = pd.to_numeric(
                    df[col],
                    errors="coerce"
                )

        # =========================
        # ORDENA
        # =========================

        if "data" in df.columns:

            df = df.sort_values(
                "data"
            )

        # =========================
        # RESET INDEX
        # =========================

        df.reset_index(
            drop=True,
            inplace=True
        )

        return df

    except Exception as e:

        st.error(
            f"Erro ao carregar {station_file}: {e}"
        )

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

    return df[
        df["data"] >= start
    ]