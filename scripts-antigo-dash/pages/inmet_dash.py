
import streamlit as st
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import locale, datetime
from concurrent.futures import ThreadPoolExecutor
import regex as re
import glob


caminho = Path('C:\\Users\\gabriel.pereira\\Documents\\plataforma-meteorologia-censipam-front\\scripts-antigo-dash\\datasets\\inmet')
st.markdown("""
            <style>
            .custom-title {
            font-size:40px;
            font-weight:bold;
            margin-top:-80px;
            margin-bottom:60px;
            text-align:left;
            color:black
            }
            </style>
            """,unsafe_allow_html=True)
st.markdown('<div class="custom-title">Dados das Estações - INMET</div>',unsafe_allow_html=True)

def carregar_dados_arquivo(arquivo, colunas_necessarias):
    dado = pd.read_csv(arquivo, parse_dates=["index"], index_col="index", usecols=colunas_necessarias,
                         dtype={'Temp. Max. (C)': 'float32', 
                                'Temp. Min. (C)': 'float32',
                                'Umi. Max. (%)': 'float32', 
                                'Umi. Min. (%)': 'float32',
                                'Vel. Vento (m/s)': 'float32',
                                'Dir. Vento (m/s)': 'float32',
                                'Chuva (mm)': 'float32'}) 
    
    #dado.index = dado.index.tz_localize("UTC").tz_convert("America/Manaus") 
    return dado


arquivos = [arquivo for arquivo in caminho.iterdir() if arquivo.is_file() and arquivo.suffix == '.csv']
cidades = [cidade.stem for cidade in caminho.iterdir() if cidade.is_file() and cidade.suffix == '.csv']
#arquivos = sorted(glob.glob(f'{caminho}/*.csv'))
#cidades    = [re.findall(r'([^/]+)\.csv$',x)[0] for x in resultados]
#resultados = dict(zip(cidades,resultados))
dados = {}
colunas_necessarias = ['index', 'Temp. Max. (C)', 'Temp. Min. (C)', 'Umi. Max. (%)', 
                       'Umi. Min. (%)', 'Vel. Vento (m/s)', 'Dir. Vento (m/s)', 'Chuva (mm)']

with ThreadPoolExecutor() as executor:
    resultados = list(executor.map(lambda arquivo: (arquivo.stem, carregar_dados_arquivo(arquivo, colunas_necessarias)), arquivos))

for cidade, dado in resultados:
    dados[cidade] = dado


st.markdown("""
            <style>
            [data-testid="stSelectbox"] {
            margin-top:-40px;
            padding: 10px;
            background-color:none;
            border-radius:0px;
            }
            div[data-testid="stMarkdownContainer"] p {
            font-size: 18px;
            font-weight: 600;
            }
            """,unsafe_allow_html=True)

st.markdown("""
            <style>
            [data-testid="stRadio"] {
            margin-top:-25px;
            padding: 10px;
            background-color:none;
            border-radius:0px;
            }
            div[data-testid="stMarkdownContainer"] p {
            font-size: 18px;
            font-weight: 500;
            }
            """,unsafe_allow_html=True)
    
with st.sidebar: 
    sel_cidade = st.selectbox('Qual estação a ser analisada?', cidades, index=11)
    if sel_cidade:
        try:
            df_cidade = dados[f'{sel_cidade}']
            data1 = df_cidade.index.min().date()
            data2 = df_cidade.index.max().date()
        except FileNotFoundError:
                st.error('Arquivo não encontrado')
        except Exception as e:
                st.error(f'Ocorreu um erro: {e} ')
        produtoi = st.radio('O que será'' analisado?', ['Dados do Dia','Resumos Diários','Eventos Extremos', 'Ranqueamento Diário'])
st.markdown("""
            <style>
            .stDateInput {
                margin-top: -100px;
                         }
             </style>
            """, unsafe_allow_html=True)

if produtoi == 'Dados do Dia':
    st.markdown('<p style="font-size:20px;margin-top:-100px;color:black">Qual dia analisar?</p>',unsafe_allow_html=True)
    data = st.date_input("",format='DD/MM/YYYY', max_value=datetime.datetime.today())
    df = df_cidade[df_cidade.index.strftime('%Y-%m-%d')== data.strftime('%Y-%m-%d')]
    prec = df['Chuva (mm)']
    vento = df[['Vel. Vento (m/s)', 'Dir. Vento (m/s)']]
    vento.columns = ['Vel.','Dire.']
    nbins = 8
    bins  = np.linspace(0,360,nbins+1)
    vento.loc[:,'dir_bin'] = pd.cut(vento['Dire.'],bins=bins, labels = ['N','NE','E','SE','S','SO','O','NO'], include_lowest=True)
    umax = df['Umi. Max. (%)']
    umin = df['Umi. Min. (%)']
    tmax = df['Temp. Max. (C)']
    tmin = df['Temp. Min. (C)']
    tidx = tmin.index.strftime('%d/%m/%Y')
    vento_rosa = vento.groupby('dir_bin', observed=False).agg({'Vel.':['median','count']}).reset_index() 
    vento_rosa.columns = ['Dire.','Vel.','Contar']
    
    
    figT = make_subplots(specs=[[{'secondary_y':False}]])
    figT.add_trace(go.Scatter(x=tmax.index,y=tmax,name='Temp. Máx.',line=dict(color='red'),mode='lines+markers',marker_symbol='circle'),secondary_y=False)
    figT.add_trace(go.Scatter(x=tmax.index,y=tmin,name='Temp. Min.',line=dict(color='blue'),mode='lines+markers',marker_symbol='circle'),secondary_y=False)
    figT.update_layout(height=400, width=600, margin={'l': 20, 'r': 20, 't': 0, 'b': 0}, 
                       legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99))

    figU = make_subplots(specs=[[{'secondary_y':False}]])
    figU.add_trace(go.Scatter(x=tmax.index,y=umax,name='Umi. Máx.',line=dict(color='#004343'),mode='lines+markers',marker_symbol='circle'),secondary_y=False)
    figU.add_trace(go.Scatter(x=tmax.index,y=umin,name='Umi. Min.',line=dict(color='#c7522a'),mode='lines+markers',marker_symbol='circle'),secondary_y=False)
    figU.update_layout(height=400, width=600, margin={'l': 20, 'r': 20, 't': 0, 'b': 0},
                       legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99))
        
    col1,col2 = st.columns(2)
    col1.subheader('Temperatura (°C)')
    col2.subheader('Umidade (%)')
    col1.plotly_chart(figT,use_container_width=True)
    col2.plotly_chart(figU,use_container_width=True)
    
    
    figPrec = go.Figure(go.Bar(name='Prec',x=prec.index,y=prec))
    tot_prec = prec.sum()
    figPrec.add_annotation(text=f'Total acumulado: {tot_prec:.1f} mm', xref='paper', yref='paper', x=1, y=1, showarrow=False, font=dict(size=18, color='black'), align='right')
    
    figVT = go.Figure(px.bar_polar(vento_rosa,r='Contar',theta='Dire.',color='Vel.',color_continuous_scale = px.colors.sequential.YlGnBu,template = 'ggplot2'))
	
    col1,col2 = st.columns(2) 
    col1.subheader('Precipitação (mm)')
    col1.plotly_chart(figPrec,use_container_width=True)
    col2.plotly_chart(figVT,use_container_width=True)


if produtoi == 'Resumos Diários':
    datas = st.date_input('Selecione o período:', (data2 - datetime.timedelta(days=7), data2), data1, data2, format='DD/MM/YYYY')
    if len(datas) == 2:
        dia_ini = pd.to_datetime(datas[0])
        dia_fim =pd.to_datetime(f'{datas[1]} 23:00')
        #dia_ini = pd.Timestamp(dia_ini).tz_localize("UTC").tz_convert("America/Manaus")
        #dia_fim = pd.Timestamp(dia_fim).tz_localize("UTC").tz_convert("America/Manaus")
        df = df_cidade.loc[(df_cidade.index >= dia_ini) & (df_cidade.index <= dia_fim)]
        prec = df['Chuva (mm)'].resample('1d').sum()
        tot_prec = prec.sum()
        vento = df[['Vel. Vento (m/s)', 'Dir. Vento (m/s)']]
        vento.columns = ['Vel.','Dire.']
        nbins = 8
        bins  = np.linspace(0,360,nbins+1)
        vento.loc[:,'dir_bin'] = pd.cut(vento['Dire.'],bins=bins, labels = ['N','NE','E','SE','S','SO','O','NO'], include_lowest=True)
        vento_rosa = vento.groupby('dir_bin', observed=False).agg({'Vel.':['median','count']}).reset_index()
        vento_rosa.columns = ['Dire.','Vel.','Contar']
        umax = df['Umi. Max. (%)'].resample('1d').max()
        umin = df['Umi. Min. (%)'].resample('1d').min()
        tmax = df['Temp. Max. (C)'].resample('1d').max()
        tmin = df['Temp. Min. (C)'].resample('1d').min()
        tidx = tmin.index.strftime('%d/%m/%Y')
        
        figT = make_subplots(specs=[[{'secondary_y':False}]])
        figT.add_trace(go.Scatter(x=tmax.index,y=tmax,name='Temp. Máx.',line=dict(color='red'),mode='lines+markers',marker_symbol='circle'),secondary_y=False)
        figT.add_trace(go.Scatter(x=tmax.index,y=tmin,name='Temp. Min.',line=dict(color='blue'),mode='lines+markers',marker_symbol='circle'),secondary_y=False)
        figT.update_layout(height=400, width=600, margin={'l': 20, 'r': 20, 't': 0, 'b': 0}, font =dict(color='blue'), 
                           legend=dict(yanchor="top",orientation='h', y=1.02, xanchor="right", x=1.02), 
                           xaxis=dict(title='Data',             title_font=dict(color='black', size=14, family='Arial Black'), tickfont=dict(color='black', size=12, family='Arial Black'), tickformat="%d/%m/%Y"),
                           yaxis=dict(title='Temperatura (°C)', title_font=dict(color='black', size=14, family='Arial Black'), tickfont=dict(color='black', size=12, family='Arial Black')))
        
        figU = make_subplots(specs=[[{'secondary_y':False}]])
        figU.add_trace(go.Scatter(x=tmax.index,y=umax,name='Umi. Máx.',line=dict(color='#004343'),mode='lines+markers',marker_symbol='circle'),secondary_y=False)
        figU.add_trace(go.Scatter(x=tmax.index,y=umin,name='Umi. Min.',line=dict(color='#c7522a'),mode='lines+markers',marker_symbol='circle'),secondary_y=False)
        figU.update_layout(height=400, width=600, margin={'l': 20, 'r': 20, 't': 0, 'b': 0},
                           legend=dict(yanchor="top",orientation='h', y=1.02, xanchor="right", x=1.02),
                           xaxis=dict(title='Data',             title_font=dict(color='black', size=14, family='Arial Black'), tickfont=dict(color='black', size=12, family='Arial Black'), tickformat="%d/%m/%Y"),
                           yaxis=dict(title='Umidade (%)', title_font=dict(color='black', size=14, family='Arial Black'), tickfont=dict(color='black', size=12, family='Arial Black')))
        
        col1,col2 = st.columns(2)
        col1.subheader('Temperatura (°C)')
        col2.subheader('Umidade (%)')
        col1.plotly_chart(figT,use_container_width=True)
        col2.plotly_chart(figU,use_container_width=True)
        
        figPrec = go.Figure(go.Bar(name='Prec',x=prec.index,y=prec))
        figPrec.update_layout(height=400, width=600, margin={'l': 20, 'r': 20, 't': 0, 'b': 0},
                              legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
                              xaxis=dict(title='Data',             title_font=dict(color='black', size=14, family='Arial Black'), tickfont=dict(color='black', size=12, family='Arial Black'), tickformat="%d/%m/%Y"),
                              yaxis=dict(title='Precipitação (mm)', title_font=dict(color='black', size=14, family='Arial Black'), tickfont=dict(color='black', size=12, family='Arial Black')))
        figPrec.add_annotation(text=f'Total acumulado: {tot_prec:.1f} mm', xref='paper', yref='paper', x=1, y=1, showarrow=False, font=dict(size=18, color='black'), align='right')
        
        figVT = go.Figure(px.bar_polar(vento_rosa,r='Contar',theta='Dire.',color='Vel.',color_continuous_scale = px.colors.sequential.YlGnBu, template = 'ggplot2'))
        
        col1,col2 = st.columns(2)
        col1.subheader('Precipitação (mm)')
        col1.plotly_chart(figPrec,use_container_width=True)
        col2.plotly_chart(figVT,use_container_width=True)

    
if produtoi == 'Eventos Extremos':
    ordem    = {'Descendente':False, 'Ascendente':True}
    ordemsel = st.selectbox('Qual ordem mostrar?', ordem.keys())
    anos = df_cidade.index.year.unique().tolist()[1:]
    anos = ['Todos os anos'] + anos[::-1]
    meses = sorted(df_cidade.index.month.unique().tolist())
    meses = ['Todos os meses'] + meses
    
    
    col_ano, col_mes = st.columns(2)
    with col_ano:
        sel_ano = st.selectbox("Selecione o ano", anos)
    with col_mes:
        sel_mes = st.selectbox("Selecione o mês", meses)

    if sel_ano == "Todos os anos" and sel_mes == "Todos os meses":
        st.markdown(""" <style> .stRadio { margin-bottom: -20px; }  </style> """, unsafe_allow_html=True)
        col1,col2,col3 = st.columns(3)
        
        prec    = df_cidade['Chuva (mm)'].resample('1d').sum().astype(np.float64).round(2).sort_values(ascending=ordem[ordemsel])
        figprec = go.Figure(data=[go.Table(header=dict(values=['<b>Data</b>','<b>Precipitação (mm)</b>'], fill_color='rgb(134, 159, 231)', align='center',font=dict(size=19,family='Times New Roman',color='black')), cells=dict(values=[prec.index.strftime('%d/%m/%Y').values,prec.to_numpy()], fill_color='rgb(184, 224, 212)',  align='center', font=dict(size=19),line=dict(width=1),height = 35),columnwidth=[35,65], )])
        
        figprec.update_layout(margin=dict(l=10, r=10, t=10, b=10), autosize=False, width=500, height=600) 
        col1.plotly_chart(figprec,use_container_width=True) 
        
        tempmax = df_cidade['Temp. Max. (C)'].resample('1d').max().astype(np.float64).round(2).sort_values(ascending=ordem[ordemsel]) 
        figtmax = go.Figure(data=[go.Table(header=dict(values=['<b>Data</b>','<b>Tempeartura Máx. (°C)</b>'], fill_color='rgb(134, 159, 231)', align='center', font=dict(size=19,family='Times New Roman',color='black')), cells=dict(values=[tempmax.index.strftime('%d/%m/%Y').values,tempmax.to_numpy()], fill_color='rgb(184, 224, 212)', align='center', font=dict(size=19),line=dict(width=1),height = 35), columnwidth=[35,65], )]) 
        figtmax.update_layout(margin=dict(l=10, r=10, t=10, b=10), autosize=False, width=500, height=600) 
        col2.plotly_chart(figtmax,use_container_width=True) 
        
        tempmin = df_cidade['Temp. Min. (C)'].resample('1d').min().astype(np.float64).round(2).sort_values(ascending=ordem[ordemsel]) 
        figtmin = go.Figure(data=[go.Table(header=dict(values=['<b>Data</b>','<b>Tempeartura Min. (°C)</b>'], fill_color='rgb(134, 159, 231)', align='center', font=dict(size=19,family='Times New Roman',color='black')), cells=dict(values=[tempmin.index.strftime('%d/%m/%Y').values,tempmin.to_numpy()], fill_color='rgb(184, 224, 212)', align='center', font=dict(size=19),line=dict(width=1),height = 35), columnwidth=[35,65], )]) 
        figtmin.update_layout(margin=dict(l=10, r=10, t=10, b=10), autosize=False,  width=500, height=600)
        col3.plotly_chart(figtmin,use_container_width=True)
        
    elif sel_ano == 'Todos os anos': 
        mes      = int(sel_mes) 
        col1,col2,col3 = st.columns(3)
        
        prec    = df_cidade['Chuva (mm)'].resample('1d').sum().astype(np.float64).round(2).sort_values(ascending=ordem[ordemsel]) 
        prec    = prec[prec.index.month == mes]
        figprec = go.Figure(data=[go.Table(header=dict(values=['<b>Data</b>','<b>Precipitação (mm)</b>'], fill_color='rgb(134, 159, 231)', align='center',font=dict(size=19,family='Times New Roman',color='black')), cells=dict(values=[prec.index.strftime('%d/%m/%Y').values,prec.to_numpy()], fill_color='rgb(184, 224, 212)',  align='center', font=dict(size=19),line=dict(width=1),height = 35),columnwidth=[35,65], )])
        figprec.update_layout(margin=dict(l=10, r=10, t=10, b=10), autosize=False, width=500, height=600) 
        col1.plotly_chart(figprec,use_container_width=True) 
        
        tempmax = df_cidade['Temp. Max. (C)'].resample('1d').max().astype(np.float64).round(2).sort_values(ascending=ordem[ordemsel])
        tempmax = tempmax[tempmax.index.month == mes]
        figtmax = go.Figure(data=[go.Table(header=dict(values=['<b>Data</b>','<b>Tempeartura Máx. (°C)</b>'], fill_color='rgb(134, 159, 231)', align='center', font=dict(size=19,family='Times New Roman',color='black')), cells=dict(values=[tempmax.index.strftime('%d/%m/%Y').values,tempmax.to_numpy()], fill_color='rgb(184, 224, 212)', align='center', font=dict(size=19),line=dict(width=1),height = 35), columnwidth=[35,65], )]) 
        figtmax.update_layout(margin=dict(l=10, r=10, t=10, b=10), autosize=False, width=500, height=600) 
        col2.plotly_chart(figtmax,use_container_width=True) 
        
        tempmin = df_cidade['Temp. Min. (C)'].resample('1d').min().astype(np.float64).round(2).sort_values(ascending=ordem[ordemsel]) 
        tempmin = tempmin[tempmin.index.month == mes]
        figtmin = go.Figure(data=[go.Table(header=dict(values=['<b>Data</b>','<b>Tempeartura Min. (°C)</b>'], fill_color='rgb(134, 159, 231)', align='center', font=dict(size=19,family='Times New Roman',color='black')), cells=dict(values=[tempmin.index.strftime('%d/%m/%Y').values,tempmin.to_numpy()], fill_color='rgb(184, 224, 212)', align='center', font=dict(size=19),line=dict(width=1),height = 35), columnwidth=[35,65], )]) 
        figtmin.update_layout(margin=dict(l=10, r=10, t=10, b=10), autosize=False,  width=500, height=600)
        col3.plotly_chart(figtmin,use_container_width=True)
        
		
    elif sel_mes == 'Todos os meses':
        ano      = int(sel_ano) 
        col1,col2,col3 = st.columns(3)
        
        prec    = df_cidade['Chuva (mm)'].resample('1d').sum().astype(np.float64).round(2).sort_values(ascending=ordem[ordemsel]) 
        prec    = prec[prec.index.year == ano]
        figprec = go.Figure(data=[go.Table(header=dict(values=['<b>Data</b>','<b>Precipitação (mm)</b>'], fill_color='rgb(134, 159, 231)', align='center',font=dict(size=19,family='Times New Roman',color='black')), cells=dict(values=[prec.index.strftime('%d/%m/%Y').values,prec.to_numpy()], fill_color='rgb(184, 224, 212)',  align='center', font=dict(size=19),line=dict(width=1),height = 35),columnwidth=[35,65], )])
        figprec.update_layout(margin=dict(l=10, r=10, t=10, b=10), autosize=False, width=500, height=600) 
        col1.plotly_chart(figprec,use_container_width=True) 
        
        tempmax = df_cidade['Temp. Max. (C)'].resample('1d').max().astype(np.float64).round(2).sort_values(ascending=ordem[ordemsel])
        tempmax = tempmax[tempmax.index.year == ano]
        figtmax = go.Figure(data=[go.Table(header=dict(values=['<b>Data</b>','<b>Tempeartura Máx. (°C)</b>'], fill_color='rgb(134, 159, 231)', align='center', font=dict(size=19,family='Times New Roman',color='black')), cells=dict(values=[tempmax.index.strftime('%d/%m/%Y').values,tempmax.to_numpy()], fill_color='rgb(184, 224, 212)', align='center', font=dict(size=19),line=dict(width=1),height = 35), columnwidth=[35,65], )]) 
        figtmax.update_layout(margin=dict(l=10, r=10, t=10, b=10), autosize=False, width=500, height=600) 
        col2.plotly_chart(figtmax,use_container_width=True) 
        
        tempmin = df_cidade['Temp. Min. (C)'].resample('1d').min().astype(np.float64).round(2).sort_values(ascending=ordem[ordemsel]) 
        tempmin = tempmin[tempmin.index.year == ano]
        figtmin = go.Figure(data=[go.Table(header=dict(values=['<b>Data</b>','<b>Tempeartura Min. (°C)</b>'], fill_color='rgb(134, 159, 231)', align='center', font=dict(size=19,family='Times New Roman',color='black')), cells=dict(values=[tempmin.index.strftime('%d/%m/%Y').values,tempmin.to_numpy()], fill_color='rgb(184, 224, 212)', align='center', font=dict(size=19),line=dict(width=1),height = 35), columnwidth=[35,65], )]) 
        figtmin.update_layout(margin=dict(l=10, r=10, t=10, b=10), autosize=False,  width=500, height=600)
        col3.plotly_chart(figtmin,use_container_width=True) 
    else:
        ano      = int(sel_ano) 
        mes      = int(sel_mes)
        
        col1,col2,col3 = st.columns(3)
        prec    = df_cidade['Chuva (mm)'].resample('1d').sum().astype(np.float64).round(2).sort_values(ascending=ordem[ordemsel]) 
        prec    = prec[prec.index.month == mes]
        prec    = prec[prec.index.year == ano]
        figprec = go.Figure(data=[go.Table(header=dict(values=['<b>Data</b>','<b>Precipitação (mm)</b>'], fill_color='rgb(134, 159, 231)', align='center',font=dict(size=19,family='Times New Roman',color='black')), cells=dict(values=[prec.index.strftime('%d/%m/%Y').values,prec.to_numpy()], fill_color='rgb(184, 224, 212)',  align='center', font=dict(size=19),line=dict(width=1),height = 35),columnwidth=[35,65], )])
        figprec.update_layout(margin=dict(l=10, r=10, t=10, b=10), autosize=False, width=500, height=600) 
        col1.plotly_chart(figprec,use_container_width=True) 
        
        tempmax = df_cidade['Temp. Max. (C)'].resample('1d').max().astype(np.float64).round(2).sort_values(ascending=ordem[ordemsel])
        tempmax = tempmax[tempmax.index.month == mes]
        tempmax = tempmax[tempmax.index.year == ano]
        figtmax = go.Figure(data=[go.Table(header=dict(values=['<b>Data</b>','<b>Tempeartura Máx. (°C)</b>'], fill_color='rgb(134, 159, 231)', align='center', font=dict(size=19,family='Times New Roman',color='black')), cells=dict(values=[tempmax.index.strftime('%d/%m/%Y').values,tempmax.to_numpy()], fill_color='rgb(184, 224, 212)', align='center', font=dict(size=19),line=dict(width=1),height = 35), columnwidth=[35,65], )]) 
        figtmax.update_layout(margin=dict(l=10, r=10, t=10, b=10), autosize=False, width=500, height=600) 
        col2.plotly_chart(figtmax,use_container_width=True) 
        
        tempmin = df_cidade['Temp. Min. (C)'].resample('1d').min().astype(np.float64).round(2).sort_values(ascending=ordem[ordemsel]) 
        tempmin = tempmin[tempmin.index.month == mes]
        tempmin = tempmin[tempmin.index.year == ano]
        figtmin = go.Figure(data=[go.Table(header=dict(values=['<b>Data</b>','<b>Tempeartura Min. (°C)</b>'], fill_color='rgb(134, 159, 231)', align='center', font=dict(size=19,family='Times New Roman',color='black')), cells=dict(values=[tempmin.index.strftime('%d/%m/%Y').values,tempmin.to_numpy()], fill_color='rgb(184, 224, 212)', align='center', font=dict(size=19),line=dict(width=1),height = 35), columnwidth=[35,65], )]) 
        figtmin.update_layout(margin=dict(l=10, r=10, t=10, b=10), autosize=False,  width=500, height=600)
        col3.plotly_chart(figtmin,use_container_width=True)


if produtoi == 'Ranqueamento Diário':
    sel_data = st.date_input("Qual dia analisar?",format='DD/MM/YYYY')
    ordem    = {'Descendente':False, 'Ascendente':True}
    ordemsel = st.selectbox('Qual ordem mostrar?', ordem.keys())
    data = pd.to_datetime(sel_data).date()
    dados_filtrados = {cidade: df[df.index.date == data] for cidade, df in dados.items()}
    
    df_concatenado = pd.concat(dados_filtrados, names=['Município'])
    df_concatenado = df_concatenado.reset_index(level=0)  


    
    col1,col2,col3 = st.columns(3)
    prec = (df_concatenado.groupby('Município')['Chuva (mm)'].resample('1D').sum().astype(np.float64).round(2).sort_values(ascending=ordem[ordemsel])).reset_index(level=0)
    
    figprec = go.Figure(data=[go.Table(header=dict(values=['<b>Município</b>','<b>Chuva (mm)</b>'],            fill_color='rgb(134, 159, 231)', align='center',font=dict(size=19,family='Times New Roman',color='black')), cells=dict(values=[prec['Município'],prec['Chuva (mm)'].to_numpy()], fill_color='rgb(184, 224, 212)',  align='center', font=dict(size=19),line=dict(width=1),height = 35),columnwidth=[75,55], )])
    figprec.update_layout(margin=dict(l=10, r=10, t=10, b=10), autosize=False, width=500, height=600) 
    col1.plotly_chart(figprec,use_container_width=True) 
    
    tempmax = (df_concatenado.groupby('Município')['Temp. Max. (C)'].resample('1D').max().astype(np.float64).round(2).sort_values(ascending=ordem[ordemsel])).reset_index(level=0)
    figtmax = go.Figure(data=[go.Table(header=dict(values=['<b>Município</b>','<b>Temp. Máx. (°C)</b>'], fill_color='rgb(134, 159, 231)', align='center', font=dict(size=19,family='Times New Roman',color='black')), cells=dict(values=[tempmax['Município'],tempmax['Temp. Max. (C)'].to_numpy()], fill_color='rgb(184, 224, 212)', align='center', font=dict(size=19),line=dict(width=1),height = 35), columnwidth=[75,55], )]) 
    figtmax.update_layout(margin=dict(l=10, r=10, t=10, b=10), autosize=False, width=500, height=600) 
    col2.plotly_chart(figtmax,use_container_width=True) 
    
    
    tempmin = (df_concatenado.groupby('Município')['Temp. Min. (C)'].resample('1d').min().astype(np.float64).round(2).sort_values(ascending=ordem[ordemsel])).reset_index(level=0)
    figtmin = go.Figure(data=[go.Table(header=dict(values=['<b>Município</b>','<b>Temp. Min. (°C)</b>'], fill_color='rgb(134, 159, 231)', align='center', font=dict(size=19,family='Times New Roman',color='black')), cells=dict(values=[tempmin['Município'],tempmin['Temp. Min. (C)'].to_numpy()], fill_color='rgb(184, 224, 212)', align='center', font=dict(size=19),line=dict(width=1),height = 35), columnwidth=[75,55], )]) 
    figtmin.update_layout(margin=dict(l=10, r=10, t=10, b=10), autosize=False,  width=500, height=600)
    col3.plotly_chart(figtmin,use_container_width=True)
