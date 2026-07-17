# dashboard_validacao.py
"""
Painel de Validação Científica — várias formas de visualizar o resultado do
validador_completo.py dentro do Streamlit.

Este arquivo expõe UMA função pronta para ser chamada de dentro do seu
ecmwf-merge.py:

    from dashboard_validacao import render_painel_validacao
    render_painel_validacao()

Ele cuida de: rodar (ou reaproveitar o cache) a validação do dia inteiro,
mostrar o placar geral, gráficos de evolução por hora, comparação por
métrica, e um mapa espacial do erro para o horário selecionado.
"""

import os

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from validador_completo import (
    carregar_cache,
    carregar_ecmwf,
    carregar_merge,
    regradear,
    resumo_veredito,
    validar_dia_comparativo,
    _selecionar_horario_mais_proximo,
    _listar_arquivos_merge_do_dia,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(BASE_DIR, "dados")

# Rótulo -> caminho do .nc. Ajuste aqui se os nomes dos arquivos mudarem.
SIMULACOES_PADRAO = {
    "Com Nudging": os.path.join(PASTA_DADOS, "dd19735e1a81a17da86a9589ac5d1bfa.nc"),
    "Sem Nudging": os.path.join(PASTA_DADOS, "6b1b424d99bfc6fab01a0390722e15c1.nc"),
}

CAMINHO_CACHE = os.path.join(PASTA_DADOS, "validacao_cache.json")

METRICAS_INFO = {
    "rmse":    {"nome": "RMSE (mm)",      "melhor": "menor"},
    "mae":     {"nome": "MAE (mm)",       "melhor": "menor"},
    "bias":    {"nome": "Bias (mm)",      "melhor": "zero"},
    "pearson": {"nome": "Correlação",     "melhor": "maior"},
    "ssim":    {"nome": "SSIM",           "melhor": "maior"},
    "pod":     {"nome": "POD",            "melhor": "maior"},
    "far":     {"nome": "FAR",            "melhor": "menor"},
    "csi":     {"nome": "CSI",            "melhor": "maior"},
    "ets":     {"nome": "ETS",            "melhor": "maior"},
    "fbi":     {"nome": "FBI",            "melhor": "um"},
}


# =============================================================================
# EXECUÇÃO / CACHE
# =============================================================================
def _rodar_validacao_com_progresso(pasta_merge, data_str, simulacoes, limiar_mm):
    barra = st.progress(0.0, text="Iniciando validação...")

    def callback(atual, total, rotulo):
        barra.progress(atual / total, text=f"Validando {rotulo} ({atual}/{total})")

    df = validar_dia_comparativo(
        pasta_merge=pasta_merge,
        data_str=data_str,
        simulacoes=simulacoes,
        limiar_mm=limiar_mm,
        salvar_json=CAMINHO_CACHE,
        progresso_callback=callback,
    )
    barra.empty()
    return df


@st.cache_data(show_spinner=False)
def _carregar_cache_cacheado(caminho, assinatura):
    """assinatura força o Streamlit a invalidar o cache quando o arquivo muda de mtime."""
    return carregar_cache(caminho)


def _obter_dados(data_str, simulacoes, limiar_mm, forcar_recalculo=False):
    if not forcar_recalculo and os.path.exists(CAMINHO_CACHE):
        mtime = os.path.getmtime(CAMINHO_CACHE)
        df = _carregar_cache_cacheado(CAMINHO_CACHE, mtime)
        if df is not None and not df.empty and (df["data"] == data_str).any():
            return df[df["data"] == data_str].reset_index(drop=True)

    return _rodar_validacao_com_progresso(PASTA_DADOS, data_str, simulacoes, limiar_mm)


# =============================================================================
# COMPONENTES VISUAIS
# =============================================================================
def _cartao_veredito(df):
    resumo = resumo_veredito(df)
    if resumo.empty:
        st.warning("Nenhum horário foi validado com sucesso ainda.")
        return

    vencedora = resumo.iloc[0]["simulacao"]
    st.subheader("🏆 Veredito da Rodada")

    colunas = st.columns(len(resumo))
    for col, (_, linha) in zip(colunas, resumo.iterrows()):
        destaque = linha["simulacao"] == vencedora
        with col:
            st.metric(
                label=f"{'🟢 ' if destaque else '🔴 '}{linha['simulacao']}",
                value=f"{linha['rmse_medio']:.3f} mm (RMSE)",
                delta=f"SSIM {linha['ssim_medio']:.2f} · POD {linha['pod_medio']:.2f}",
                delta_color="off",
            )

    melhor_rmse = resumo.iloc[0]["rmse_medio"]
    pior_rmse = resumo.iloc[-1]["rmse_medio"]
    if pior_rmse > 0:
        ganho_pct = ((pior_rmse - melhor_rmse) / pior_rmse) * 100
        st.success(
            f"**{vencedora}** foi a simulação mais próxima do observado (MERGE), "
            f"com um RMSE {ganho_pct:.1f}% menor que a pior rodada, "
            f"validado em {int(resumo.iloc[0]['horas_validadas'])} horário(s)."
        )


def _tabela_detalhada(df):
    with st.expander("📋 Tabela detalhada (todas as horas e métricas)"):
        colunas_exibir = ["horario", "simulacao", "rmse", "mae", "bias",
                           "pearson", "ssim", "pod", "far", "csi", "ets", "fbi", "status"]
        colunas_exibir = [c for c in colunas_exibir if c in df.columns]
        st.dataframe(
            df[colunas_exibir].style.format(
                {c: "{:.3f}" for c in colunas_exibir if c not in ("horario", "simulacao", "status")},
                na_rep="—",
            ),
            use_container_width=True,
            hide_index=True,
        )


def _serie_temporal(df, metrica):
    ok = df[df["status"] == "ok"]
    if ok.empty or metrica not in ok.columns:
        return

    info = METRICAS_INFO.get(metrica, {"nome": metrica, "melhor": "menor"})
    fig = px.line(
        ok.sort_values("timestamp"),
        x="horario",
        y=metrica,
        color="simulacao",
        markers=True,
        title=f"Evolução de {info['nome']} ao longo do dia",
        labels={"horario": "Horário (UTC)", metrica: info["nome"], "simulacao": "Simulação"},
    )
    fig.update_layout(hovermode="x unified", legend_title_text="")
    st.plotly_chart(fig, use_container_width=True, key=f"serie_{metrica}")


def _comparativo_barras(df):
    resumo = resumo_veredito(df)
    if resumo.empty:
        return

    colunas_metricas = ["rmse_medio", "mae_medio", "ssim_medio", "pod_medio", "csi_medio", "ets_medio"]
    colunas_metricas = [c for c in colunas_metricas if c in resumo.columns]

    longo = resumo.melt(
        id_vars="simulacao", value_vars=colunas_metricas,
        var_name="metrica", value_name="valor",
    )
    longo["metrica"] = longo["metrica"].str.replace("_medio", "", regex=False)

    fig = px.bar(
        longo, x="metrica", y="valor", color="simulacao", barmode="group",
        title="Comparativo de métricas médias do dia",
        labels={"metrica": "Métrica", "valor": "Valor médio", "simulacao": "Simulação"},
    )
    st.plotly_chart(fig, use_container_width=True, key="comparativo_barras")


def _radar_desempenho(df):
    resumo = resumo_veredito(df)
    if resumo.empty:
        return

    # Normaliza cada métrica para 0-1 (maior = melhor) para caber no radar
    eixos = ["ssim_medio", "pearson_medio", "pod_medio", "csi_medio", "ets_medio"]
    eixos = [e for e in eixos if e in resumo.columns]
    rotulos = [e.replace("_medio", "").upper() for e in eixos]

    fig = go.Figure()
    for _, linha in resumo.iterrows():
        valores = [max(0, min(1, linha[e])) if linha[e] == linha[e] else 0 for e in eixos]
        fig.add_trace(go.Scatterpolar(
            r=valores + [valores[0]],
            theta=rotulos + [rotulos[0]],
            fill="toself",
            name=linha["simulacao"],
        ))
    fig.update_layout(
        title="Radar de desempenho (quanto maior a área, melhor)",
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
    )
    st.plotly_chart(fig, use_container_width=True, key="radar_desempenho")


def _mapa_espacial_erro(data_str, simulacoes, horario_str, limiar_mm):
    """Recalcula (sob demanda) o campo observado, simulado e a diferença espacial
    para um horário específico e desenha os três mapas lado a lado."""
    arquivos = _listar_arquivos_merge_do_dia(PASTA_DADOS, data_str)
    alvo = None
    for caminho, ts in arquivos:
        if ts.strftime("%H:%M") == horario_str:
            alvo = (caminho, ts)
            break
    if alvo is None:
        st.info("Sem arquivo MERGE para este horário.")
        return

    caminho_merge, timestamp = alvo
    da_merge = carregar_merge(caminho_merge)

    abas = st.tabs(list(simulacoes.keys()))
    for aba, (rotulo, caminho_nc) in zip(abas, simulacoes.items()):
        with aba:
            da_ecmwf = carregar_ecmwf(caminho_nc)
            fatia, _ = _selecionar_horario_mais_proximo(da_ecmwf, timestamp)
            if fatia is None:
                st.info("Sem horário correspondente dentro da tolerância.")
                continue
            regrid = regradear(fatia, da_merge)

            obs = da_merge.values
            sim = regrid.values
            if np.nanmax(sim) < 1.0 and np.nanmax(obs) > 1.0:
                sim = sim * 1000.0
            diferenca = sim - obs

            chave_base = f"{data_str}_{horario_str}_{rotulo}".replace(" ", "_").replace(":", "")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.plotly_chart(
                    px.imshow(obs, origin="lower", color_continuous_scale="Blues",
                              title="MERGE (observado)", labels={"color": "mm"}),
                    use_container_width=True,
                    key=f"mapa_obs_{chave_base}",
                )
            with col2:
                st.plotly_chart(
                    px.imshow(sim, origin="lower", color_continuous_scale="Blues",
                              title=f"ECMWF — {rotulo}", labels={"color": "mm"}),
                    use_container_width=True,
                    key=f"mapa_sim_{chave_base}",
                )
            with col3:
                limite = float(np.nanmax(np.abs(diferenca))) or 1.0
                st.plotly_chart(
                    px.imshow(diferenca, origin="lower", color_continuous_scale="RdBu_r",
                              zmin=-limite, zmax=limite,
                              title="Diferença (Simulado − Observado)", labels={"color": "mm"}),
                    use_container_width=True,
                    key=f"mapa_diff_{chave_base}",
                )


def _dispersao_pixel_a_pixel(data_str, simulacoes, horario_str):
    arquivos = _listar_arquivos_merge_do_dia(PASTA_DADOS, data_str)
    alvo = next((item for item in arquivos if item[1].strftime("%H:%M") == horario_str), None)
    if alvo is None:
        return
    caminho_merge, timestamp = alvo
    da_merge = carregar_merge(caminho_merge)

    linhas = []
    for rotulo, caminho_nc in simulacoes.items():
        da_ecmwf = carregar_ecmwf(caminho_nc)
        fatia, _ = _selecionar_horario_mais_proximo(da_ecmwf, timestamp)
        if fatia is None:
            continue
        regrid = regradear(fatia, da_merge)
        obs = da_merge.values.ravel()
        sim = regrid.values.ravel()
        if np.nanmax(sim) < 1.0 and np.nanmax(obs) > 1.0:
            sim = sim * 1000.0
        mascara = ~np.isnan(obs) & ~np.isnan(sim)
        # amostra até 4000 pontos para o gráfico não travar o navegador
        idx = np.where(mascara)[0]
        if idx.size > 4000:
            idx = np.random.choice(idx, 4000, replace=False)
        for o, s in zip(obs[idx], sim[idx]):
            linhas.append({"observado_mm": o, "simulado_mm": s, "simulacao": rotulo})

    if not linhas:
        return
    df_disp = pd.DataFrame(linhas)
    maximo = max(df_disp["observado_mm"].max(), df_disp["simulado_mm"].max())

    fig = px.scatter(
        df_disp, x="observado_mm", y="simulado_mm", color="simulacao",
        opacity=0.4, title="Dispersão pixel a pixel (observado x simulado)",
        labels={"observado_mm": "MERGE observado (mm)", "simulado_mm": "ECMWF simulado (mm)"},
    )
    fig.add_shape(type="line", x0=0, y0=0, x1=maximo, y1=maximo,
                  line=dict(dash="dash", color="gray"))
    chave = f"dispersao_{data_str}_{horario_str}".replace(" ", "_").replace(":", "")
    st.plotly_chart(fig, use_container_width=True, key=chave)


# =============================================================================
# ENTRYPOINT
# =============================================================================
def render_painel_validacao(data_str=None, simulacoes=None, limiar_mm=1.0):
    """Chame esta função dentro do seu app Streamlit para desenhar o painel inteiro."""
    st.subheader("🛰️ Validação Científica — MERGE (observado) x ECMWF (simulado)")

    simulacoes = simulacoes or SIMULACOES_PADRAO

    col_data, col_limiar, col_botao = st.columns([2, 1, 1])
    with col_data:
        data_str = st.text_input("Data para validar (AAAAMMDD)", value=data_str or "20260601")
    with col_limiar:
        limiar_mm = st.number_input("Limiar de evento de chuva (mm)", value=float(limiar_mm), step=0.5)
    with col_botao:
        st.write("")
        st.write("")
        recalcular = st.button("🔄 Recalcular")

    faltando = [r for r, c in simulacoes.items() if not os.path.exists(c)]
    if faltando:
        st.error(f"Arquivo(s) .nc não encontrado(s) para: {', '.join(faltando)}. "
                  f"Verifique a pasta `dados/`.")
        return

    try:
        with st.spinner("Carregando validação (usa cache se disponível)..."):
            df = _obter_dados(data_str, simulacoes, limiar_mm, forcar_recalculo=recalcular)
    except FileNotFoundError as erro:
        st.error(str(erro))
        return

    if df is None or df.empty:
        st.info("Sem dados para este dia.")
        return

    _cartao_veredito(df)
    st.markdown("---")

    aba_series, aba_comparativo, aba_mapas, aba_dispersao, aba_tabela = st.tabs(
        ["📈 Séries por hora", "📊 Comparativo", "🗺️ Mapas espaciais", "🎯 Dispersão", "📋 Tabela"]
    )

    with aba_series:
        metrica_escolhida = st.selectbox(
            "Métrica", list(METRICAS_INFO.keys()),
            format_func=lambda m: METRICAS_INFO[m]["nome"],
        )
        _serie_temporal(df, metrica_escolhida)

    with aba_comparativo:
        _comparativo_barras(df)
        _radar_desempenho(df)

    with aba_mapas:
        horarios_ok = sorted(df[df["status"] == "ok"]["horario"].unique())
        if horarios_ok:
            horario_sel = st.select_slider("Horário", options=horarios_ok, value=horarios_ok[0])
            _mapa_espacial_erro(data_str, simulacoes, horario_sel, limiar_mm)
        else:
            st.info("Nenhum horário válido para mapear.")

    with aba_dispersao:
        horarios_ok = sorted(df[df["status"] == "ok"]["horario"].unique())
        if horarios_ok:
            horario_sel2 = st.select_slider("Horário ", options=horarios_ok, value=horarios_ok[0], key="disp")
            _dispersao_pixel_a_pixel(data_str, simulacoes, horario_sel2)

    with aba_tabela:
        _tabela_detalhada(df)


if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Validação Meteorológica")
    render_painel_validacao()