import os
import calendar
import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import streamlit as st
from boltons import iterutils
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from services.acumula_mes_2clima import carregar_acumulado_observado

import xarray as xr
xr.set_options(use_new_combine_kwarg_defaults=True)

# ==========================================
# CONSTANTES E CAMINHOS BASE
# ==========================================
CAMINHO_BASE_MERGE = Path("src/assets/dados/MERGE")
CAMINHO_CLIMO = CAMINHO_BASE_MERGE / "CLIMATOLOGY"
CAMINHO_GRIBS = Path("datasets/gribs")  # Ajuste conforme estrutura real
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
    if not CAMINHO_CSV.exists():
        return pd.DataFrame(columns=["nome", "latitude", "longitude", "uf"])
    df = pd.read_csv(CAMINHO_CSV)
    if "uf" in df.columns:
        df = df[df["uf"].astype(str).str.upper() == "AM"]
    elif "codigo_uf" in df.columns:
        df = df[df["codigo_uf"] == 13]
    return df.sort_values("nome").reset_index(drop=True)

def dividir_dias_mes(ano: int, mes: int, freq: int):
    ndias = calendar.monthrange(ano, mes)[1] + 1
    dias = [datetime.date(ano, mes, dia).strftime('%Y%m%d') for dia in range(1, ndias)]
    
    divd = list(iterutils.chunked(dias, freq))
    
    if len(divd[-1]) == 1:
        if freq == 15 and len(divd) > 2:
            divd[1] = divd[1] + divd[-1]
            divd = divd[:2]
        elif freq == 10 and len(divd) > 3:
            divd[2] = divd[2] + divd[-1]
            divd = divd[:3]
            
    return divd

@st.cache_data
def extrair_quantis_estacao(lat_cid, lon_cid, tipo_escala="mensal", num_periodo=1):
    tagarea = "reg_amazonia_bacia_amazonas"
    
    if tipo_escala in ["mensal", "Mês"]:
        nome_npy = f"distri_MERGE_mensal_{tagarea}.npy"
    elif tipo_escala in ["quinzena", "Quinzena"]:
        nome_npy = f"distri_MERGE_{num_periodo}_quinzena_{tagarea}.npy"
    else:
        nome_npy = f"distri_MERGE_{num_periodo}_decendio_{tagarea}.npy"
        
    arq_npy = CAMINHO_CLIMO / nome_npy
    arq_lat = CAMINHO_CLIMO / f"latitude_merge_{tagarea}.txt"
    arq_lon = CAMINHO_CLIMO / f"longitude_merge_{tagarea}.txt"
    
    if not (arq_npy.exists() and arq_lat.exists() and arq_lon.exists()):
        print(f"⚠️ Arquivos de climatologia não encontrados em: {CAMINHO_CLIMO}")
        return None
        
    lat_grid = np.loadtxt(arq_lat)
    lon_grid = np.loadtxt(arq_lon)
    
    idx_lat = np.abs(lat_grid - lat_cid).argmin()
    idx_lon = np.abs(lon_grid - lon_cid).argmin()
    
    distri = np.load(arq_npy)
    return distri[:, :, idx_lat, idx_lon]

def extrair_precipitacao_observada(ano: int, lat_cid: float, lon_cid: float, escala: str, sub_idx: int = 1):
    precip_obs = []
    is_parcial = []  # Lista para sinalizar períodos incompletos
    
    for m in range(1, 13):
        val = np.nan
        parcial = False
        try:
            if escala in ["Mês", "Mensal"]:
                print(f"📂 Verificando acumulado mensal observado: {m:02d}/{ano}...")
                
                ndias_mes = calendar.monthrange(ano, m)[1]
                pasta_mes = CAMINHO_GRIBS / str(ano) / f"{m:02d}"
                if not pasta_mes.exists():
                    pasta_mes = CAMINHO_BASE_MERGE / str(ano) / f"{m:02d}"
                
                dias_esperados = [
                    str(pasta_mes / f"MERGE_CPTEC_{ano}{m:02d}{d:02d}.grib2")
                    for d in range(1, ndias_mes + 1)
                ]
                arqs_existentes = [f for f in dias_esperados if Path(f).exists()]
                
                if not arqs_existentes:
                    precip_obs.append(np.nan)
                    is_parcial.append(False)
                    continue

                if len(arqs_existentes) < ndias_mes:
                    parcial = True
                    print(f"⚠️ Mês {m:02d}/{ano} incompleto ({len(arqs_existentes)}/{ndias_mes} dias). Calculando acumulado parcial.")

                ds_mes = carregar_acumulado_observado(ano, m)
                lon_t = lon_cid
                if "longitude" in ds_mes.coords and ds_mes.longitude.max() > 180 and lon_t < 0:
                    lon_t = 360 + lon_t
                elif "lon" in ds_mes.coords and ds_mes.lon.max() > 180 and lon_t < 0:
                    lon_t = 360 + lon_t

                var_prec = next((v for v in ["prec", "pacum", "precip"] if v in ds_mes.data_vars), list(ds_mes.data_vars)[0])
                
                if "latitude" in ds_mes.coords:
                    val = ds_mes[var_prec].sel(latitude=lat_cid, longitude=lon_t, method="nearest").values.item()
                else:
                    val = ds_mes[var_prec].sel(lat=lat_cid, lon=lon_t, method="nearest").values.item()

            else:
                freq = 10 if escala == "Decêndio" else 15
                div_dias = dividir_dias_mes(ano, m, freq)
                
                if sub_idx - 1 < len(div_dias):
                    dias_sub = div_dias[sub_idx - 1]
                    qtd_dias_esperados = len(dias_sub)

                    pasta_mes = CAMINHO_GRIBS / str(ano) / f"{m:02d}"
                    if not pasta_mes.exists():
                        pasta_mes = CAMINHO_BASE_MERGE / str(ano) / f"{m:02d}"

                    arqs_sub = [
                        str(pasta_mes / f"MERGE_CPTEC_{d_str}.grib2")
                        for d_str in dias_sub
                        if (pasta_mes / f"MERGE_CPTEC_{d_str}.grib2").exists()
                    ]
                    
                    if arqs_sub:
                        if len(arqs_sub) < qtd_dias_esperados:
                            parcial = True
                            print(f"⚠️ {escala} {sub_idx} de {m:02d}/{ano} incompleto ({len(arqs_sub)}/{qtd_dias_esperados} dias). Calculando acumulado parcial.")

                        ds_sub = xr.open_mfdataset(
                            arqs_sub,
                            engine="cfgrib",
                            combine="nested",
                            concat_dim="time",
                            coords='minimal',
                            compat='override',
                            parallel=False,
                            backend_kwargs={
                                "filter_by_keys": {"typeOfLevel": "surface"},
                                "indexpath": ""
                            }
                        )
                        ds_soma = ds_sub.sum(dim="time", keep_attrs=True)
                        
                        lon_t = lon_cid
                        if "longitude" in ds_soma.coords and ds_soma.longitude.max() > 180 and lon_t < 0:
                            lon_t = 360 + lon_t
                        elif "lon" in ds_soma.coords and ds_soma.lon.max() > 180 and lon_t < 0:
                            lon_t = 360 + lon_t
                            
                        var_prec = "prec" if "prec" in ds_soma.data_vars else list(ds_soma.data_vars)[0]
                        if "latitude" in ds_soma.coords:
                            val = ds_soma[var_prec].sel(latitude=lat_cid, longitude=lon_t, method="nearest").values.item()
                        else:
                            val = ds_soma[var_prec].sel(lat=lat_cid, lon=lon_t, method="nearest").values.item()

        except Exception as e:
            print(f"❌ Erro ao processar mês {m}/{ano} na escala {escala}: {str(e)}")
            val = np.nan
            parcial = False
            
        precip_obs.append(val)
        is_parcial.append(parcial)
        
    return precip_obs, is_parcial


# ==========================================
# RENDERIZAÇÃO DE GRÁFICOS (PLOTLY)
# ==========================================
def criar_grafico_clima(cidade, ano, mes_nome, escala, quantis, precip_obs_tuple, sub_periodo=None):
    fig = go.Figure()
    meses_labels = [m[:3] for m in LISTA_MESES]
    
    if isinstance(precip_obs_tuple, tuple):
        precip_obs, is_parcial = precip_obs_tuple
    else:
        precip_obs, is_parcial = precip_obs_tuple, [False]*12

    if quantis is not None and quantis.shape[1] == 4:
        p15, p35, p65, p85 = quantis[:, 0], quantis[:, 1], quantis[:, 2], quantis[:, 3]
        
        fig.add_trace(go.Scatter(
            x=meses_labels, y=p15, name="Muito Seco (< P15)", 
            fill='tozeroy', fillcolor='rgba(248, 194, 69, 0.4)', 
            line=dict(color='rgba(0,0,0,0)'),
            hovertemplate="<b>%{y:.2f}</b><extra><b>%{fullData.name}</b></extra>"
        ))
        fig.add_trace(go.Scatter(
            x=meses_labels, y=p35, name="Seco (P15–P35)", 
            fill='tonexty', fillcolor='rgba(253, 250, 172, 0.5)', 
            line=dict(color='rgba(0,0,0,0)'),
            hovertemplate="<b>%{y:.2f}</b><extra><b>%{fullData.name}</b></extra>"
        ))
        fig.add_trace(go.Scatter(
            x=meses_labels, y=p65, name="Normal", 
            fill='tonexty', fillcolor='rgba(226, 232, 240, 0.6)', 
            line=dict(color='rgba(0,0,0,0)'),
            hovertemplate="<b>%{y:.2f}</b><extra><b>%{fullData.name}</b></extra>"
        ))
        fig.add_trace(go.Scatter(
            x=meses_labels, y=p85, name="Chuvoso (P65–P85)", 
            fill='tonexty', fillcolor='rgba(187, 239, 249, 0.5)', 
            line=dict(color='rgba(0,0,0,0)'),
            hovertemplate="<b>%{y:.2f}</b><extra><b>%{fullData.name}</b></extra>"
        ))
        
        # Ajuste para mostrar o valor real de P85 no tooltip de "Muito Chuvoso" e preencher até a borda superior do eixo Y
        fig.add_trace(go.Scatter(
            x=meses_labels, y=p85, name="Muito Chuvoso (> P85)", 
            fill='tonexty', fillcolor='rgba(37, 99, 235, 0.15)', 
            line=dict(color='rgba(0,0,0,0)'),
            hovertemplate="<b>%{y:.2f}</b><extra><b>%{fullData.name}</b></extra>"
        ))

    # Constrói o texto do hover dinamicamente para o Observado
    hover_texts_obs = []
    for v, p in zip(precip_obs, is_parcial):
        if np.isnan(v):
            hover_texts_obs.append("")
        elif p:
            hover_texts_obs.append(f"⚠️ Acumulado parcial: {v:.2f}")
        else:
            hover_texts_obs.append(f"{v:.2f}")

    fig.add_trace(go.Scatter(
        x=meses_labels, y=precip_obs, name=f"Observado ({ano})",
        mode='lines+markers+text',
        text=[f"{v:.1f}" if not np.isnan(v) else "" for v in precip_obs],
        textposition="top center",
        line=dict(color='darkblue', width=3),
        marker=dict(size=8, color='orange'),
        hovertext=hover_texts_obs,
        hovertemplate="<b>%{hovertext}</b><extra><b>%{fullData.name}</b></extra>"
    ))

    sub_tit = f" — {sub_periodo}º {escala.upper()}" if sub_periodo else ""
    fig.update_layout(
        title=f"<b>Precipitação vs. Climatologia — {cidade} ({mes_nome}/{ano}){sub_tit}</b>",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20), height=380,
        font=dict(color="black"),
        hoverlabel=dict(
            font_size=12,
            font_family="Arial",
            font_color="black"
        ),
        xaxis=dict(
            title=dict(text="<b>Mês</b>", font=dict(color="black", size=14)),
            tickfont=dict(color="black", style="normal", family="Arial Black")
        ),
        yaxis=dict(
            title=dict(text="<b>Chuva (mm)</b>", font=dict(color="black", size=14)),
            tickfont=dict(color="black", style="normal", family="Arial Black"),
            range=[0, 500]  # Fixa a escala do eixo Y até 500 mm
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(color="black", size=12, family="Arial")
        )
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

    c1, c2, c3 = st.columns([2, 2, 3])
    with c1:
        st.markdown('<div class="filter-label">MUNICÍPIO (AM)</div>', unsafe_allow_html=True)
        municipio_sel = st.selectbox("Município", df_am["nome"].unique(), label_visibility="collapsed")
    with c2:
        st.markdown('<div class="filter-label">PRODUTO</div>', unsafe_allow_html=True)
        tipo_viz = st.radio("Produto", ["Gráficos Individuais", "Comparativo"], horizontal=True, label_visibility="collapsed")
    with c3:
        st.markdown('<div class="filter-label">ESCALA TEMPORAL</div>', unsafe_allow_html=True)
        opcoes_escala = ["Decêndio", "Quinzena", "Mês"] if tipo_viz == "Gráficos Individuais" else ["Mês"]
        escala = st.radio("Escala Temporal", opcoes_escala, horizontal=True, label_visibility="collapsed")

    info_cidade = df_am[df_am["nome"] == municipio_sel].iloc[0]
    lat_cid, lon_cid = info_cidade["latitude"], info_cidade["longitude"]

    st.markdown("---")

    # MODO 1: GRÁFICOS INDIVIDUAIS
    if tipo_viz == "Gráficos Individuais":
        col_ano, col_mes = st.columns(2)
        with col_ano:
            st.markdown('<div class="filter-label">ANO</div>', unsafe_allow_html=True)
            ano_sel = st.selectbox("Ano", ["2026", "2025", "2024", "2023"], key="ano_ind_graf", label_visibility="collapsed")
        with col_mes:
            st.markdown('<div class="filter-label">MÊS</div>', unsafe_allow_html=True)
            mes_sel = st.selectbox("Mês", LISTA_MESES, key="mes_ind_graf", label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)

        if escala == "Mês":
            quantis = extrair_quantis_estacao(lat_cid, lon_cid, tipo_escala="mensal")
            precip_obs = extrair_precipitacao_observada(int(ano_sel), lat_cid, lon_cid, "Mês")
            fig = criar_grafico_clima(municipio_sel, ano_sel, mes_sel, "Mês", quantis, precip_obs)
            st.plotly_chart(fig, width="stretch")
        else:
            qtd_periodos = 3 if escala == "Decêndio" else 2
            tipo_npy = "decendio" if escala == "Decêndio" else "quinzena"

            for i in range(1, qtd_periodos + 1):
                quantis = extrair_quantis_estacao(lat_cid, lon_cid, tipo_escala=tipo_npy, num_periodo=i)
                precip_obs = extrair_precipitacao_observada(int(ano_sel), lat_cid, lon_cid, escala, i)
                
                fig = criar_grafico_clima(municipio_sel, ano_sel, mes_sel, escala, quantis, precip_obs, sub_periodo=i)
                st.plotly_chart(fig, width="stretch")
                st.markdown("<br>", unsafe_allow_html=True)

    # MODO 2: COMPARATIVO MENSAL (Um abaixo do outro)
    else:
        st.subheader("📊 Comparativo Mensal de Dois Anos")
        c_a1, c_a2 = st.columns(2)
        with c_a1:
            st.markdown('<div class="filter-label">PRIMEIRO ANO</div>', unsafe_allow_html=True)
            ano1 = st.selectbox("Primeiro Ano", ["2026", "2025", "2024", "2023"], index=1, key="comp_ano1", label_visibility="collapsed")
        with c_a2:
            st.markdown('<div class="filter-label">SEGUNDO ANO</div>', unsafe_allow_html=True)
            ano2 = st.selectbox("Segundo Ano", ["2026", "2025", "2024", "2023"], index=0, key="comp_ano2", label_visibility="collapsed")

        quantis_m = extrair_quantis_estacao(lat_cid, lon_cid, tipo_escala="mensal")
        precip_obs1 = extrair_precipitacao_observada(int(ano1), lat_cid, lon_cid, "Mês")
        precip_obs2 = extrair_precipitacao_observada(int(ano2), lat_cid, lon_cid, "Mês")

        fig1 = criar_grafico_clima(municipio_sel, ano1, "Geral", "Mês", quantis_m, precip_obs1)
        st.plotly_chart(fig1, width="stretch")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        fig2 = criar_grafico_clima(municipio_sel, ano2, "Geral", "Mês", quantis_m, precip_obs2)
        st.plotly_chart(fig2, width="stretch")