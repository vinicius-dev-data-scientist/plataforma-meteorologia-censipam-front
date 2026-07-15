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
                ["Últimos 30 dias", "Últimos 15 dias", "Este mês"],
                index=0
            )

        with col_v:
            # Lista de métricas expandida conforme solicitado
            opcao_metrica = st.selectbox(
                "MÉTRICA",
                [
                    "Temperatura Máxima (°C)", 
                    "Temperatura Mínima (°C)", 
                    "Precipitação Acumulada (> 15mm)", 
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
            # Define o comportamento padrão da ordenação dependendo da métrica escolhida
            default_index = 0
            if "Mínima" in opcao_metrica:
                default_index = 1  # Para temperatura mínima, o padrão mais interessante é o menor valor (recorde de frio)

            ordem_sel = st.selectbox(
                "ORDENAÇÃO",
                ["Maiores valores", "Menores valores"],
                index=default_index
            )

    # Mapeamento dinâmico das variáveis para as colunas físicas do CSV
    if "Máxima" in opcao_metrica:
        col_alvo = "temp_max"
        prefixo_var = "Temp. Máx"
        sufixo_unidade = " °C"
        cor_barras = "#E05353"  # Vermelho quente
    elif "Mínima" in opcao_metrica:
        col_alvo = "temp_min"
        prefixo_var = "Temp. Mín"
        sufixo_unidade = " °C"
        cor_barras = "#06B6D4"  # Azul ciano/frio
    elif "Precipitação" in opcao_metrica:
        col_alvo = "chuva"
        prefixo_var = "Chuva"
        sufixo_unidade = " mm"
        cor_barras = "#3B82F6"  # Azul escuro
    else: # Maior Rajada
        col_alvo = "vento_raj"
        prefixo_var = "Rajada"
        sufixo_unidade = " m/s"
        cor_barras = "#8B5CF6"  # Roxo

    # =====================================================
    # COMPILAÇÃO DOS DADOS DE TODAS AS ESTAÇÕES
    # =====================================================
    lista_registros = []

    with st.spinner("🌡️ Compilando registros das estações..."):
        for nome_estacao, arquivo_csv in stations.items():
            df_estacao = load_station_data(arquivo_csv)
            
            if df_estacao.empty or "data" not in df_estacao.columns or col_alvo not in df_estacao.columns:
                continue
                
            # Filtra pelo período selecionado
            df_filtrado = filter_period(df_estacao, periodo)
            
            if df_filtrado.empty:
                continue
                
            # Remove valores nulos
            df_filtrado = df_filtrado.dropna(subset=[col_alvo])
            
            # REGRA: Se for chuva, exibir estritamente valores maiores que 15mm
            if col_alvo == "chuva":
                df_filtrado = df_filtrado[df_filtrado[col_alvo] > 15]
            
            for _, row in df_filtrado.iterrows():
                lista_registros.append({
                    "estacao": nome_estacao,
                    "data_registro": row["data"],
                    "valor": row[col_alvo]
                })

    if not lista_registros:
        st.warning("⚠️ Nenhum registro encontrado para a métrica e período selecionados (Nota: Chuva exibe apenas valores > 15mm).")
        st.stop()

    # Cria o DataFrame unificado
    df_geral = pd.DataFrame(lista_registros)

    # Aplica Ordenação
    ascendente = True if ordem_sel == "Menores valores" else False
    df_ranking = df_geral.sort_values(by="valor", ascending=ascendente).head(top_n)

    # Formatação de string da Data e Rótulo Combinado
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
        labels={"valor": opcao_metrica, "Estação (Data)": "Estação / Data do Registro"}
    )

    fig.update_traces(
        marker_color=cor_barras,
        texttemplate=f'%{{text:.1f}}{sufixo_unidade}',
        textposition='inside',
        insidetextanchor='end',
        hovertemplate='<b>%{y}</b><br>' + f'{prefixo_var}: ' + '<b>%{x:.1f}' + f'{sufixo_unidade}</b><extra></extra>'
    )

    fig.update_layout(
        xaxis_title=opcao_metrica,
        yaxis_title=None,
        margin=dict(l=20, r=20, t=10, b=10),
        height=120 + (top_n * 32),  # Altura dinâmica proporcional
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12)
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor='#F3F4F6',
        zeroline=False
    )
    
    fig.update_yaxes(
        tickmode='linear',
        showgrid=False
    )

    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    render()