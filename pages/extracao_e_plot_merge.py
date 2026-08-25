import os
import calendar
import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import streamlit as st
from boltons import iterutils
import glob
import plotly.graph_objects as go

# ==========================================
# CONSTANTES E CAMINHOS BASE
# ==========================================
CAMINHO_BASE_MERGE = Path("src/assets/dados/MERGE")
CAMINHO_CLIMO = CAMINHO_BASE_MERGE / "CLIMATOLOGY"
CAMINHO_CSV = Path("src/assets/dados/munis_sele_180.csv")

LISTA_MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]
MES_MAP = {m: i + 1 for i, m in enumerate(LISTA_MESES)}
MESES_ABR = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

# ==========================================
# FUNÇÕES DE SUPORTE E LÓGICA TEMPORAL
# ==========================================
@st.cache_data
def carregar_municipios_am():
    """Carrega o CSV e filtra estritamente municípios do Amazonas."""
    if not CAMINHO_CSV.exists():
        return pd.DataFrame(columns=["nome", "latitude", "longitude", "uf"])
    df = pd.read_csv(CAMINHO_CSV)
    if "uf" in df.columns:
        df = df[df["uf"].astype(str).str.upper() == "AM"]
    elif "codigo_uf" in df.columns:
        df = df[df["codigo_uf"] == 13]
    return df.sort_values("nome").reset_index(drop=True)

def dividir_dias_mes(ano: int, mes: int, freq: int):
    """
    Divide os dias do mês de acordo com a frequência (10 para decêndio, 15 para quinzena).
    Ajusta o último bloco caso a sobra seja 1 dia.
    """
    ndias = calendar.monthrange(ano, mes)[1] + 1
    dias = [datetime.date(ano, mes, dia).strftime('%Y%m%d') for dia in range(1, ndias)]
    
    # Divisão utilizando iterutils.chunked exatamente como no script original
    divd = iterutils.chunked(dias, freq)
    
    if len(divd[-1]) == 1:
        if freq == 15:
            divd[1] = divd[1] + divd[-1]
            divd = divd[:2]
        elif freq == 10:
            divd[2] = divd[2] + divd[-1]
            divd = divd[:3]
            
    return divd

@st.cache_data
def extrair_quantis_estacao(lat_cid, lon_cid, tipo_escala="mensal", num_periodo=1):
    """Obtém os quantis P15, P35, P65, P85 da distribuição .npy para uma lat/lon."""
    tagarea = "reg_amazonia_bacia_amazonas"
    
    if tipo_escala == "mensal":
        nome_npy = f"distri_MERGE_mensal_{tagarea}.npy"
    elif tipo_escala == "quinzena":
        nome_npy = f"distri_MERGE_{num_periodo}_quinzena_{tagarea}.npy"
    else: # decendio
        nome_npy = f"distri_MERGE_{num_periodo}_decendio_{tagarea}.npy"
        
    arq_npy = CAMINHO_CLIMO / nome_npy
    arq_lat = CAMINHO_CLIMO / f"latitude_merge_{tagarea}.txt"
    arq_lon = CAMINHO_CLIMO / f"longitude_merge_{tagarea}.txt"
    
    if not (arq_npy.exists() and arq_lat.exists() and arq_lon.exists()):
        return None
        
    lat_grid = np.loadtxt(arq_lat)
    lon_grid = np.loadtxt(arq_lon)
    
    idx_lat = np.abs(lat_grid - lat_cid).argmin()
    idx_lon = np.abs(lon_grid - lon_cid).argmin()
    
    distri = np.load(arq_npy)
    return distri[:, :, idx_lat, idx_lon]

def extrair_precipitacao_observada(ano: int, lat_cid: float, lon_cid: float, escala: str, sub_idx: int = 1):
    """Extrai precipitação observada para os 12 meses seguindo o ano e sub-período especificados."""
    precip_obs = []
    
    for m in range(1, 13):
        val = np.nan
        try:
            if escala == "Mês":
                str_mes_abr = MESES_ABR[m - 1]
                padrão_arq = f"*_{str_mes_abr}_{ano}.nc"
                arqs = list((CAMINHO_BASE_MERGE / "MONTHLY").glob(padrão_arq))
                if arqs:
                    ds = xr.open_dataset(arqs[0])
                    val = ds["pacum"].sel(lat=lat_cid, lon=lon_cid, method="nearest").values.item()
            else:
                freq = 10 if escala == "Decêndio" else 15
                div_dias = dividir_dias_mes(ano, m, freq)
                if sub_idx - 1 < len(div_dias):
                    dias_sub = div_dias[sub_idx - 1]
                    soma_sub = 0.0
                    contou = False
                    for d_str in dias_sub:
                        tagfl = f"{CAMINHO_BASE_MERGE}/Diario/{ano}/{m:02d}/*{d_str}*.grib2"
                        fl = glob.glob(tagfl)
                        if fl:
                            grb = xr.open_dataset(fl[0], engine='cfgrib', decode_timedelta=True)
                            lon_t = lon_cid
                            if grb.longitude.max() > 180 and lon_t < 0:
                                lon_t = 360 + lon_t
                            val_d = grb['prec'].sel(latitude=lat_cid, longitude=lon_t, method='nearest').values.item()
                            soma_sub += val_d
                            contou = True
                    if contou:
                        val = soma_sub
        except Exception:
            val = np.nan
        precip_obs.append(val)
    return precip_obs

# ==========================================
# RENDERIZAÇÃO DE GRÁFICOS (PLOTLY)
# ==========================================
def criar_grafico_clima(cidade, ano, mes_nome, escala, quantis, precip_obs, sub_periodo=None):
    fig = go.Figure()
    meses_labels = [m[:3] for m in LISTA_MESES]
    
    if quantis is not None and quantis.shape[1] == 4:
        p15, p35, p65, p85 = quantis[:, 0], quantis[:, 1], quantis[:, 2], quantis[:, 3]
        
        fig.add_trace(go.Scatter(x=meses_labels, y=p15, name="Muito Seco (< P15)", fill='tozeroy', fillcolor='rgba(248, 194, 69, 0.4)', line=dict(color='rgba(0,0,0,0)')))
        fig.add_trace(go.Scatter(x=meses_labels, y=p35, name="Seco (P15–P35)", fill='tonexty', fillcolor='rgba(253, 250, 172, 0.5)', line=dict(color='rgba(0,0,0,0)')))
        fig.add_trace(go.Scatter(x=meses_labels, y=p65, name="Normal", fill='tonexty', fillcolor='rgba(226, 232, 240, 0.6)', line=dict(color='rgba(0,0,0,0)')))
        fig.add_trace(go.Scatter(x=meses_labels, y=p85, name="Chuvoso (P65–P85)", fill='tonexty', fillcolor='rgba(187, 239, 249, 0.5)', line=dict(color='rgba(0,0,0,0)')))
        
        y_max = max(np.nanmax(p85) * 1.2 if not np.isnan(p85).all() else 100, 50)
        fig.add_trace(go.Scatter(x=meses_labels, y=[y_max]*12, name="Muito Chuvoso (> P85)", fill='tonexty', fillcolor='rgba(37, 99, 235, 0.15)', line=dict(color='rgba(0,0,0,0)')))

    fig.add_trace(go.Scatter(
        x=meses_labels, y=precip_obs, name=f"Observado ({ano})",
        mode='lines+markers+text',
        text=[f"{v:.1f}" if not np.isnan(v) else "" for v in precip_obs],
        textposition="top center",
        line=dict(color='darkblue', width=3),
        marker=dict(size=8, color='orange')
    ))

    sub_tit = f" — {sub_periodo}º {escala.upper()}" if sub_periodo else ""
    fig.update_layout(
        title=f"<b>Precipitação vs. Climatologia — {cidade} ({mes_nome}/{ano}){sub_tit}</b>",
        xaxis_title="Mês", yaxis_title="Chuva (mm)",
        hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20), height=380
    )
    return fig

# ==========================================
# PÁGINA PRINCIPAL
# ==========================================
def render():
    st.markdown("""
    <div class="main-title">Extração e Plotagem MERGE · Gráficos Climatológicos</div>
    <div class="subtitle">Análise temporal de precipitação por município do Amazonas</div>
    """, unsafe_allow_html=True)

    df_am = carregar_municipios_am()
    if df_am.empty:
        st.error("Nenhum município do Amazonas foi localizado no arquivo munis_sele_180.csv.")
        return

    # Filtros Superiores Principais
    c1, c2, c3 = st.columns([2, 2, 3])
    with c1:
        st.markdown('<div class="filter-label">MUNICÍPIO (AM)</div>', unsafe_allow_html=True)
        municipio_sel = st.selectbox("", df_am["nome"].unique())
    with c2:
        st.markdown('<div class="filter-label">PRODUTO</div>', unsafe_allow_html=True)
        tipo_viz = st.radio("", ["Gráficos Individuais", "Comparativo"], horizontal=True)
    with c3:
        st.markdown('<div class="filter-label">ESCALA TEMPORAL</div>', unsafe_allow_html=True)
        # Regra: Mensal disponível APENAS em Comparativo
        opcoes_escala = ["Decêndio", "Quinzena"] if tipo_viz == "Gráficos Individuais" else ["Mês"]
        escala = st.radio("", opcoes_escala, horizontal=True)

    info_cidade = df_am[df_am["nome"] == municipio_sel].iloc[0]
    lat_cid, lon_cid = info_cidade["latitude"], info_cidade["longitude"]

    st.markdown("---")

    # MODO 1: GRÁFICOS INDIVIDUAIS (Ano + Mês -> Mostra 3 Decêndios ou 2 Quinzenas empilhados)
    if tipo_viz == "Gráficos Individuais":
        col_ano, col_mes = st.columns(2)
        with col_ano:
            st.markdown('<div class="filter-label">ANO</div>', unsafe_allow_html=True)
            ano_sel = st.selectbox("", ["2026", "2025", "2024", "2023"], key="ano_ind_graf")
        with col_mes:
            st.markdown('<div class="filter-label">MÊS</div>', unsafe_allow_html=True)
            mes_sel = st.selectbox("", LISTA_MESES, key="mes_ind_graf")

        st.markdown("<br>", unsafe_allow_html=True)

        qtd_periodos = 3 if escala == "Decêndio" else 2
        tipo_npy = "decendio" if escala == "Decêndio" else "quinzena"

        # Gera os 3 gráficos para decêndio ou os 2 gráficos para quinzena empilhados
        for i in range(1, qtd_periodos + 1):
            quantis = extrair_quantis_estacao(lat_cid, lon_cid, tipo_escala=tipo_npy, num_periodo=i)
            precip_obs = extrair_precipitacao_observada(int(ano_sel), lat_cid, lon_cid, escala, i)
            
            fig = criar_grafico_clima(municipio_sel, ano_sel, mes_sel, escala, quantis, precip_obs, sub_periodo=i)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)

    # MODO 2: COMPARATIVO MENSAL (2 Anos Selecionados)
    else:
        st.subheader("📊 Comparativo Mensal de Dois Anos")
        c_a1, c_a2 = st.columns(2)
        with c_a1:
            st.markdown('<div class="filter-label">PRIMEIRO ANO</div>', unsafe_allow_html=True)
            ano1 = st.selectbox("", ["2026", "2025", "2024", "2023"], index=1, key="comp_ano1")
        with c_a2:
            st.markdown('<div class="filter-label">SEGUNDO ANO</div>', unsafe_allow_html=True)
            ano2 = st.selectbox("", ["2026", "2025", "2024", "2023"], index=0, key="comp_ano2")

        quantis_m = extrair_quantis_estacao(lat_cid, lon_cid, tipo_escala="mensal")
        precip_obs1 = extrair_precipitacao_observada(int(ano1), lat_cid, lon_cid, "Mês")
        precip_obs2 = extrair_precipitacao_observada(int(ano2), lat_cid, lon_cid, "Mês")

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig1 = criar_grafico_clima(municipio_sel, ano1, "Geral", "Mês", quantis_m, precip_obs1)
            st.plotly_chart(fig1, use_container_width=True)
        with col_g2:
            fig2 = criar_grafico_clima(municipio_sel, ano2, "Geral", "Mês", quantis_m, precip_obs2)
            st.plotly_chart(fig2, use_container_width=True)