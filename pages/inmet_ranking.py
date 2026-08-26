import streamlit as st
import pandas as pd
import plotly.express as px

# Importando as funções e variáveis originais do inmet_dash_plot
from pages.inmet_dash_plot import load_station_data, filter_period, stations

# =====================================================
# RENDER
# =====================================================

def render():

    st.markdown(
        """
        <div class="main-title">
            Ranking INMET
        </div>

        <div class="subtitle">
            Recordes de curto prazo monitorados pelas estações automáticas
        </div>
        """,
        unsafe_allow_html=True
    )

    # Controles de Filtros do Ranking
    with st.container(border=True):
        col_periodo, col_v, col_top, col_ordem = st.columns([0.25, 0.3, 0.15, 0.3])

        with col_periodo:
            periodo = st.selectbox(
                "PERÍODO",
                ["Últimos 30 dias", "Últimos 15 dias", "Este mês", "Por dia"],
                index=0
            )

        with col_v:
            opcao_metrica = st.selectbox(
                "MÉTRICA",
                [
                    "Temperatura Máxima (°C)", 
                    "Temperatura Mínima (°C)", 
                    "Precipitação Acumulada", 
                    "Maior Rajada de Vento (m/s)"
                ],
                index=0
            )

        with col_top:
            top_n = st.slider(
                "QUANTIDADE",
                min_value=5,
                max_value=30,
                value=15,
                step=5
            )

        with col_ordem:
            default_index = 0
            if "Mínima" in opcao_metrica:
                default_index = 1

            ordem_sel = st.selectbox(
                "ORDENAÇÃO",
                ["Maiores valores", "Menores valores"],
                index=default_index
            )

    # Se a opção escolhida for "Por dia", adiciona um seletor de data
    data_selecionada = None
    if periodo == "Por dia":
        c_date, _ = st.columns([0.3, 0.7])
        with c_date:
            data_selecionada = st.date_input("SELECIONE A DATA", value=pd.Timestamp.today().date())

    # Mapeamento dinâmico das variáveis para as colunas físicas do CSV
    if "Máxima" in opcao_metrica:
        col_alvo = "temp_max"
        prefixo_var = "Temp. Máx"
        sufixo_unidade = " °C"
        cor_barras = "#E05353"
        mode_extremo = "max"
    elif "Mínima" in opcao_metrica:
        col_alvo = "temp_min"
        prefixo_var = "Temp. Mín"
        sufixo_unidade = " °C"
        cor_barras = "#06B6D4"
        mode_extremo = "min"
    elif "Precipitação" in opcao_metrica:
        col_alvo = "chuva"
        prefixo_var = "Chuva"
        sufixo_unidade = " mm"
        cor_barras = "#3B82F6"
        mode_extremo = "sum"
    else: # Maior Rajada
        col_alvo = "vento_raj"
        prefixo_var = "Rajada"
        sufixo_unidade = " m/s"
        cor_barras = "#8B5CF6"
        mode_extremo = "max"

    # =====================================================
    # COMPILAÇÃO DOS DADOS DE TODAS AS ESTAÇÕES
    # =====================================================
    lista_registros = []

    with st.spinner("🌡️ Compilando registros das estações..."):
        for nome_estacao, arquivo_csv in stations.items():
            df_estacao = load_station_data(arquivo_csv)
            
            if df_estacao.empty or "data" not in df_estacao.columns:
                continue

            # Garante que a coluna alvo exista
            if col_alvo not in df_estacao.columns:
                df_estacao[col_alvo] = 0.0 if col_alvo == "chuva" else pd.NA
                
            # Tratamento para precipitação (substitui nulos por zero)
            if col_alvo == "chuva":
                df_estacao[col_alvo] = df_estacao[col_alvo].fillna(0.0)

            # Lógica de Filtro por Período
            if periodo == "Por dia":
                if data_selecionada is None:
                    continue
                df_filtrado = df_estacao[df_estacao["data"].dt.date == data_selecionada]
            else:
                df_filtrado = filter_period(df_estacao, periodo)
            
            if df_filtrado.empty:
                continue

            # =====================================================
            # AGREGAÇÃO DIÁRIA COM REGISTRO DA HORA
            # =====================================================
            for data_dia, df_dia in df_filtrado.groupby(df_filtrado["data"].dt.date):
                df_dia_valid = df_dia.dropna(subset=[col_alvo])
                
                if df_dia_valid.empty:
                    continue

                if mode_extremo == "sum":
                    val = df_dia_valid[col_alvo].sum()
                    dt_registro = df_dia_valid["data"].max() # Última hora registrada do dia
                elif mode_extremo == "min":
                    idx = df_dia_valid[col_alvo].idxmin()
                    val = df_dia_valid.loc[idx, col_alvo]
                    dt_registro = df_dia_valid.loc[idx, "data"]
                else: # max
                    idx = df_dia_valid[col_alvo].idxmax()
                    val = df_dia_valid.loc[idx, col_alvo]
                    dt_registro = df_dia_valid.loc[idx, "data"]

                lista_registros.append({
                    "estacao": nome_estacao,
                    "data_registro": dt_registro,
                    "valor": val
                })

    if not lista_registros:
        st.warning("⚠️ Nenhum registro encontrado para o período ou data selecionada.")
        st.stop()

    # Cria o DataFrame unificado
    df_geral = pd.DataFrame(lista_registros)

    # Aplica Ordenação
    ascendente = True if ordem_sel == "Menores valores" else False
    df_ranking = df_geral.sort_values(by="valor", ascending=ascendente).head(top_n)

    # Formatação com Data e Hora (DD/MM/AAAA HH:MM)
    df_ranking["data_fmt"] = df_ranking["data_registro"].dt.strftime("%d/%m/%Y %H:%M")

    df_ranking["Estação (Data)"] = (
        df_ranking["estacao"].astype(str).str.upper() 
        + " — " 
        + df_ranking["data_fmt"]
    )

    # Inverte para exibição correta de cima para baixo no Plotly
    df_chart = df_ranking.iloc[::-1].copy()

    # =====================================================
    # GRÁFICO PLOTLY INTERATIVO
    # =====================================================
    fig = px.bar(
        df_chart,
        x="valor",
        y="Estação (Data)",
        orientation="h",
        text="valor",
        labels={"valor": opcao_metrica, "Estação (Data)": "Estação / Data e Hora do Registro"}
    )

    fig.update_traces(
        marker_color=cor_barras,
        texttemplate=f'%{{text:.1f}}{sufixo_unidade}',
        textposition='inside',
        insidetextanchor='end',
        textfont=dict(
            color='#FFFFFF',
            size=16,
            family='Arial', 
            weight='bold'
        ),
        hovertemplate='<b>%{y}</b><br>' + f'{prefixo_var}: ' + '<b>%{x:.1f}' + f'{sufixo_unidade}</b><extra></extra>'
    )

    fig.update_layout(
        xaxis_title=opcao_metrica,
        yaxis_title=None,
        margin=dict(l=20, r=20, t=10, b=10),
        height=120 + (top_n * 32),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(
            color='#000000',
            size=12,
            family='Arial',
            weight='bold'
        )
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor='#F3F4F6',
        zeroline=False,
        tickfont=dict(color='#000000', size=12, family='Arial', weight='bold'),
        title_font=dict(size=12, family='Arial', color='#000000', weight='bold')
    )
    
    fig.update_yaxes(
        tickmode='linear',
        showgrid=False,
        tickfont=dict(color='#000000', size=12, family='Arial', weight='bold'),
        title_font=dict(size=12, family='Arial', color='#000000', weight='bold')
    )

    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    render()