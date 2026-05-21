
import streamlit as st
import folium
from folium.raster_layers import ImageOverlay
from folium.plugins import Fullscreen
from streamlit_folium import folium_static
from pathlib import Path
from PIL import Image
import io
import regex as re
import glob,os,sys
import numpy as np
from datetime import datetime,timedelta
import base64

# ======== CONSTANTES =========
lons         = [-62.3126, -57.6701]
lats         = [-5.4564, -0.8221]
# ======== xxxxxxxxxx ========

@st.cache_resource(show_spinner='Carregando as figuras de refletividade...')
def load_imagens(datrd,imgs,temps):
    rimgs = {datrd:{}}
    for c,img in enumerate(imgs):
        with open(img,'rb') as f:
            img_rd = f.read()
            rimgs[datrd][temps[c]] = img_rd
    return rimgs

def extrair_tempos(fls,pad):
    return [re.findall(pad,x)[0] for x in fls]

def muda_fmt_tempo(temps,fmti,fmto):
    return [re.sub(fmti,fmto,x) for x in temps]

def plot_fig_mapa(lons,lats,img_urls):
    cantos  = [[lats[0],lons[0]],[lats[-1],lons[-1]]]
    centlon = np.array(lons).mean()
    centlat = np.array(lats).mean()
    m = folium.Map() #locations=[centlat,centlon],zoom_start=6)
    m.fit_bounds(cantos)
    Fullscreen().add_to(m)
    overlay = ImageOverlay(image=img_urls,bounds=cantos,opacity=0.6,
    interactive=True,cross_origin=False,zindex=1)
    overlay.add_to(m)
    folium.LayerControl().add_to(m)
    folium.Rectangle(
            bounds=cantos,color='red',fill=False
            ).add_to(m)

    return m


col,_,_,_ = st.columns([0.25]*4)

st.markdown("""
        <style>
        .custom-title {
        font-size:40px;
        font-weight:bold;
        margin-top:-190px;
        text-align:left;
        color:black }
        </style>""",unsafe_allow_html=True)

st.markdown('<div class="custom-title">Imagens do CAPPI de 3 km do radar SBMN</div>',unsafe_allow_html=True)


with col:
    st.markdown("""
            <style>
            .custom-sel {
            font-size:23px;
            font-weight:bold;
            margin-top:10px;
            margin-bottom:-75px;
            color:green;
            }
            </style>""",unsafe_allow_html=True)

    st.markdown("""
            <style>
            [data-testid="stSelectbox"] {
            margin-top:10px;
            }
            </style>""",unsafe_allow_html=True)
    dataini   = datetime(2025,8,28)
    path_imgs = '/w1/RADAR_DADOS/sbmn'
    datas_usa = sorted([x[-8:] for x in glob.glob(f'{path_imgs}/2*') if datetime.strptime(x[-8:],'%Y%m%d')>=dataini])
    st.markdown('<div class="custom-sel">Qual data a ser observada?</div>',unsafe_allow_html=True)
    data = st.selectbox('',datas_usa[::-1])

imgs1    = sorted(glob.glob(f'{path_imgs}/{data}/FIGS_CAPPI/*'))
fmt_tpfl = r'\d{8}_\d{4}'
fmt_tpi  = r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})'
fmt_tpo  = r'\3/\2/\1 \4:\5'
tempsi   = extrair_tempos(imgs1,fmt_tpfl)
tempso   = muda_fmt_tempo(tempsi,fmt_tpi,fmt_tpo)
imgs1    = load_imagens(data,imgs1,tempso)

temp_img = st.select_slider('Previsão para o tempo:',options=tempso)

img64       = base64.b64encode(imgs1[data][temp_img]).decode('utf-8')
data_url    = f"data:image/png;base64,{img64}"
mapa_plot1  = plot_fig_mapa(lons,lats,data_url)
folium_static(mapa_plot1,width=1415,height=1000)


