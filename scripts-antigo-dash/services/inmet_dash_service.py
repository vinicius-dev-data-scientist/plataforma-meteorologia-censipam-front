import os
import pandas as pd

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
# LOAD CSV
# =========================
def load_station_data(station_file):

    path = os.path.join(DATASET_DIR, station_file)

    if not os.path.exists(path):
        return pd.DataFrame()

    # CSV INMET
    df = pd.read_csv(
        path,
        sep=None,
        engine="python",
        encoding="utf-8-sig"
    )

    df.columns = df.columns.str.strip()

    # remove colunas inúteis
    for col in ["Unnamed: 0", "index"]:
        if col in df.columns:
            df.drop(columns=[col], inplace=True)

    print("ANTES:")
    print(df.columns.tolist())

    df.rename(columns=COLUMN_MAP, inplace=True)

    print("DEPOIS:")
    print(df.columns.tolist())

    df["data"] = pd.to_datetime(
        df["data"],
        errors="coerce"
    )

    # converte numéricos
    numeric_cols = [
        "temp_inst",
        "temp_max",
        "temp_min",
        "umi_inst",
        "umi_max",
        "umi_min",
        "vento_vel",
        "vento_dir",
        "vento_raj",
        "chuva"
    ]

    for col in numeric_cols:

        if col in df.columns:

            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", ".")
            )

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    return df


# =========================
# FILTRO DE PERÍODO
# =========================
def filter_period(df, period):

    if df.empty:
        return df

    today = df["data"].max()

    if period == "Últimos 30 dias":

        start = today - pd.Timedelta(days=30)

    elif period == "Últimos 15 dias":

        start = today - pd.Timedelta(days=15)

    elif period == "Este mês":

        start = today.replace(day=1)

    else:

        return df

    return df[df["data"] >= start]