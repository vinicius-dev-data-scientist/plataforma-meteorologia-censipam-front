import glob
import re
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.image as mpimg
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from datetime import datetime
import xarray as xr

# ==========================================
# 1. DEFINIÇÃO DE CAMINHOS E PARÂMETROS
# ==========================================
caminho_base = Path("C:\\Users\\gabriel.pereira\\OneDrive - CENSIPAM\\Documentos\\plataforma-meteorologia-censipam-front\\src\\assets\\dados\\MERGE")
caminho_logo = Path("C:\\Users\\gabriel.pereira\\OneDrive - CENSIPAM\\Documentos\\plataforma-meteorologia-censipam-front\\static\\img\\Logo1x Censipam - Positivo.png")
caminho_merge_m = caminho_base / "MONTHLY"
caminho_merge_d = caminho_base / "DAILY"
caminho_climo = caminho_base / "CLIMATOLOGY"
caminho_csv = Path(
    "C:\\Users\\gabriel.pereira\\OneDrive - CENSIPAM\\Documentos\\plataforma-meteorologia-censipam-front\\src\\assets\\dados\\munis_sele_180.csv"
)  

ANO_ALVO = 2026
MES_ATUAL = datetime.now().month 
NOME_CIDADE = "Coari"

MESES_ABR = [
    "jan",
    "fev",
    "mar",
    "abr",
    "mai",
    "jun",
    "jul",
    "ago",
    "set",
    "out",
    "nov",
    "dez",
]

# ==========================================
# 2. LOCALIZAR COORDENADAS DA CIDADE
# ==========================================
df_munis = pd.read_csv(caminho_csv)
cidade_info = df_munis[df_munis["nome"] == NOME_CIDADE].iloc[0]
lat_cid, lon_cid = cidade_info["latitude"], cidade_info["longitude"]

print(
    f"Cidade selecionada: {NOME_CIDADE} (Lat: {lat_cid:.3f}, Lon: {lon_cid:.3f})"
)

# ==========================================
# 3. EXTRAIR QUANTIS DO NPY PARA A CIDADE
# ==========================================
lat_grid = np.loadtxt(
    caminho_climo / "latitude_merge_reg_amazonia_bacia_amazonas.txt"
)
lon_grid = np.loadtxt(
    caminho_climo / "longitude_merge_reg_amazonia_bacia_amazonas.txt"
)

idx_lat = np.abs(lat_grid - lat_cid).argmin()
idx_lon = np.abs(lon_grid - lon_cid).argmin()

distri_mensal = np.load(
    caminho_climo / "distri_MERGE_mensal_reg_amazonia_bacia_amazonas.npy"
)

quantis_cidade = distri_mensal[:, :, idx_lat, idx_lon]



# ==========================================
# 4. PROCESSAR DADOS DE PRECIPITAÇÃO (ANO ATUAL)
# ==========================================
precip_observada = []

for mes in range(1, 13):
    str_mes_abr = MESES_ABR[mes - 1]

    if mes < MES_ATUAL:
        padrão_arq = f"*_{str_mes_abr}_{ANO_ALVO}.nc"
        arquivos = list(caminho_merge_m.glob(padrão_arq))

        if arquivos:
            ds_m = xr.open_dataset(arquivos[0])
            val = (
                ds_m["pacum"]
                .sel(lat=lat_cid, lon=lon_cid, method="nearest")
                .values.item()
            )
            precip_observada.append(val)
        else:
            precip_observada.append(np.nan)
            
            

    elif mes == MES_ATUAL:
        pasta_dia_mes = caminho_merge_d / str(ANO_ALVO) / f"{mes:02d}"
        arqs_diarios = sorted(pasta_dia_mes.glob("*.grib2"))

        if not arqs_diarios:
            arqs_diarios = sorted(pasta_dia_mes.glob("MERGE_CPTEC_*"))

        if arqs_diarios:
            try:
                ds_d = xr.open_mfdataset(
                    arqs_diarios,
                    combine="nested",
                    concat_dim="time",
                    engine="cfgrib",
                    coords="minimal",
                    compat='override'
                )
            except Exception:
                ds_d = xr.open_mfdataset(
                    arqs_diarios,
                    combine="nested",
                    concat_dim="time",
                    coords="minimal",
                )

            chaves_prec = ["rdp", "prec", "pacum", "tp", "p01", "rain"]
            var_d = None
            for v in ds_d.data_vars:
                if any(k in v.lower() for k in chaves_prec):
                    var_d = v
                    break

            if not var_d:
                outras_vars = [v for v in ds_d.data_vars if v != "prmsl"]
                var_d = outras_vars[0] if outras_vars else list(ds_d.data_vars)[0]

            lat_name = "lat" if "lat" in ds_d.coords else "latitude"
            lon_name = "lon" if "lon" in ds_d.coords else "longitude"

            lon_target = lon_cid
            if ds_d[lon_name].max() > 180 and lon_target < 0:
                lon_target = 360 + lon_target

            val_acum_parcial = (
                ds_d[var_d]
                .sel(
                    {lat_name: lat_cid, lon_name: lon_target}, method="nearest"
                )
                .sum(dim="time")
                .values.item()
            )

            precip_observada.append(val_acum_parcial)
        else:
            precip_observada.append(np.nan)

# ==========================================
# 5. GERAR O GRÁFICO
# ==========================================
eixo_x = np.arange(1, 13)
nomes_meses = [
    "Jan",
    "Fev",
    "Mar",
    "Abr",
    "Mai",
    "Jun",
    "Jul",
    "Ago",
    "Set",
    "Out",
    "Nov",
    "Dez",
]

plt.figure(figsize=(11, 6), dpi=600)
alpha = 0.55
cores      = ['#f8c245','#fdfaac','#ffffff','#bbeff9','#0000ff']
if quantis_cidade.shape[1] == 4:
    p15 = quantis_cidade[:, 0]
    p35 = quantis_cidade[:, 1]
    p65 = quantis_cidade[:, 2]
    p85 = quantis_cidade[:, 3]

    plt.fill_between(
        eixo_x,
        0,
        p15,
        color=cores[0],
        alpha=alpha,
        label="Muito Seco (< P15)",
        linestyle="--",
    )

    plt.fill_between(
        eixo_x,
        p15,
        p35,
        color=cores[1],
        alpha=alpha,
        label="Seco (P15–P35)",
        linestyle="--",
    )

    plt.fill_between(
        eixo_x,
        p35,
        p65,
        color="gray",
        alpha=alpha,
        label="Normal",
        linestyle="--",
    )

    plt.fill_between(
        eixo_x,
        p65,
        p85,
        color=cores[3],
        alpha=alpha,
        label="Chuvoso (P65–P85)",
        linestyle="--",
    )

    y_max_lim = max(np.nanmax(p85) * 1.05, np.nanmax(precip_observada) * 1.15)
    plt.fill_between(
        eixo_x,
        p85,
        y_max_lim,
        color=cores[4],
        alpha=0.10,
        label="Muito Chuvoso (> P85)",
        linestyle="--",
    )


# -----------------------------------------------------------------------------
# 2. PLOT DA PRECIPITAÇÃO OBSERVADA (LINHAS E PONTOS)
# -----------------------------------------------------------------------------
obs_array = np.array(precip_observada)
indices_validos = np.where(~np.isnan(obs_array))[0]

idx_atual = MES_ATUAL - 1

if len(indices_validos) > 0:
    x_valid = eixo_x[indices_validos]
    y_valid = obs_array[indices_validos]

    plt.plot(
        x_valid,
        y_valid,
        color="darkblue",
        linewidth=1.5,
        linestyle="-",
        zorder=1,
    )

    idx_fechados = [i for i in indices_validos if i < idx_atual]
    if idx_fechados:
        plt.scatter(
            eixo_x[idx_fechados],
            obs_array[idx_fechados],
            color="darkblue",
            s=70,
            zorder=5,
            label=f"Acum. Mensal ({ANO_ALVO})",
        )

    if idx_atual in indices_validos:
        plt.scatter(
            eixo_x[idx_atual],
            obs_array[idx_atual],
            color="orange",
            edgecolor="darkred",
            linewidth=1,
            s=70,
            zorder=6,
            label="Acum. Parcial (Mês Atual)",
        )

    # Rótulos numéricos acima de cada ponto
    for x_i, y_i in zip(x_valid, y_valid):
        offset = max(y_valid) * 0.03
        xoffset =  max(x_valid) * 0.03
        plt.text(
            x_i + xoffset,
            y_i + offset,
            f"{y_i:.1f}",
            ha="left",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color="black",
            zorder=7,
        )
        
plt.suptitle(
    f"Precipitação Mensal vs. Climatologia (MERGE) \n\n {NOME_CIDADE} - {ANO_ALVO}",
    fontsize=14,
    fontweight="bold",
)

plt.xticks(eixo_x, nomes_meses, fontsize=10)
plt.ylabel("Chuva (mm)", fontsize=11)
plt.ylim(-5, y_max_lim if "y_max_lim" in locals() else None)
plt.xlim(0.9, 12.1)
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0)

plt.tight_layout()
if caminho_logo.exists():
    logo_img = mpimg.imread(caminho_logo)

    imagebox = OffsetImage(logo_img, zoom=0.06)

    ab = AnnotationBbox(
        imagebox,
        (0.98, 0.02),  
        xycoords="figure fraction",
        box_alignment=(1.0, 0.0), 
        frameon=False,  
    )

    plt.gca().add_artist(ab)
plt.show()