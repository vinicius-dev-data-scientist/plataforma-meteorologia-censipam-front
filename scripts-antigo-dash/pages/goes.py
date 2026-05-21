from pandas import options
import streamlit as st
import streamlit.components.v1 as components
import regex as re
from datetime import datetime
import os, glob
import base64, json

# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="GOES • Classificação de Tempestades",
    page_icon="🛰️",
    layout="centered",
)

path_imgs = 'C:\\Users\\gabriel.pereira\\Documents\\plataforma-meteorologia-censipam-front\\scripts-antigo-dash\\img'
hoje  = datetime.today().strftime('%Y-%m-%d')
ah, mh, dh = [int(x) for x in hoje.split('-')]

st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1660px; }
    h1 { color: #1f3a5f; }
    div[data-baseweb="select"] { width: 100% !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Cache — lê cada PNG uma única vez por data
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="📡 Carregando imagens do dia…")
def carregar_imagens(data_fmt: str):
    figs = sorted(glob.glob(f'{path_imgs}/*{data_fmt}*.png'))
    if not figs:
        return {}, []
    tps_pad = r"_(\d{4})_"
    imagens = {}
    for fig in figs:
        chave = re.findall(tps_pad, fig)
        if chave:
            with open(fig, 'rb') as f:
                imagens[chave[0]] = f.read()
    return imagens, sorted(imagens.keys())

# ---------------------------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------------------------
st.set_page_config(
page_title = "Monitoramento GOES",
page_icon = '🛰️',
layout='centered')
st.title("🛰️ Monitoramento GOES")
st.caption("Imagens de satélite e classificação de tempestades severas")

# ---------------------------------------------------------------------------
# Controles Streamlit
# ---------------------------------------------------------------------------
n_fig_fix = 2
with st.container(border=True):
    col_b, col_d = st.columns([0.25,0.75])
    with col_b:
        with st.container(border=False):
            bandas = [f'Banda-{x:.02g}' for x in range(13, 14)] + ['Banda-13: Classificação']
            prod = st.selectbox('🌎 Banda', bandas, index=len(bandas) - 1)
        with st.container(border=False):
            data = st.date_input('📅 Data', format='DD/MM/YYYY', max_value=datetime.today())
            data_fmt   = data.strftime('%Y%m%d')
            data_label = data.strftime('%d/%m/%Y')
            imagens, opcoes = carregar_imagens(data_fmt)   
            if not imagens:
                st.warning(f"⚠️ Nenhuma imagem encontrada para **{data_label}**. Tente outra data.")
                st.stop()
            opcoes_formatadas = [f"{h[:2]}:{h[2:]}" for h in opcoes]
            n_total = len(opcoes) 
    with col_d:  
        with st.container(border=False):    
            st.markdown("**🔁 Janela da animação** — Selecione o intervalo do loop")
            st.markdown('<style>div[data-testid="stRadio"] { margin-top: -60px; }</style>', unsafe_allow_html=True)
            with st.container(border=False):
                loop = st.radio('',['Por período',f'As últimas {n_fig_fix} imagens'], horizontal=True)
            if loop == 'Por período':
                idx_inicio, idx_fim = st.select_slider(
                    "Selecione o intervalo",
                    options=opcoes_formatadas,
                    value=(opcoes_formatadas[0], opcoes_formatadas[-1]),
                    label_visibility='collapsed'
                )

                h_ini = opcoes_formatadas.index(idx_inicio)#opcoes[idx_inicio]
                h_fim = opcoes_formatadas.index(idx_fim)
                
                n_selecionadas = (h_fim - h_ini) + 1
                opcoes_loop = opcoes[h_ini:h_fim+1]
                st.caption(
                f"Loop de **{idx_inicio} UTC** "
                f"até **{idx_fim} UTC** "
                f"— {n_selecionadas} de {n_total} selecionadas"
            )
            else:
                n_selecionadas = n_fig_fix
                opcoes_loop = opcoes[-n_fig_fix:]
                st.caption(
                f"Loop de **{opcoes[-n_fig_fix]} UTC** "
                f"até **{opcoes[-1]} UTC** "
                f"— {n_selecionadas} de {n_total} selecionadas"
            )

img_uris_all  = {k: f"data:image/png;base64,{base64.b64encode(v).decode()}"
                      for k, v in imagens.items()}
js_images_all = json.dumps(img_uris_all)
js_opcoes_all = json.dumps(opcoes)
js_opcoes_loop= json.dumps(opcoes_loop)

# ---------------------------------------------------------------------------
# Componente HTML/JS
# ---------------------------------------------------------------------------
html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: transparent;
  }}

  .info-bar {{
    display: flex;
    align-items: center;
    gap: 1.2rem;
    background: #f0f4f8;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    margin-bottom: 10px;
    font-size: 13px;
    color: #444;
    min-height: 38px;
  }}
  .info-bar b   {{ color: #1f3a5f; }}
  .info-bar .ct {{ margin-left: auto; color: #999; font-size: 12px; white-space: nowrap; }}

  .controls {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    flex-wrap: wrap;
  }}
  #slider {{
    flex: 1;
    min-width: 120px;
    accent-color: #ff4b4b;
    cursor: pointer;
    height: 4px;
  }}
  .btn {{
    padding: 6px 14px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    white-space: nowrap;
    transition: opacity .15s;
  }}
  .btn:hover  {{ opacity: .8; }}
  .btn-play   {{ background: #ff4b4b; color: #fff; min-width: 90px; }}
  .btn-stop   {{ background: #e2e2e2; color: #333; }}
  .btn-dl     {{ background: #1f3a5f; color: #fff; }}
  select {{
    padding: 5px 8px;
    border-radius: 6px;
    border: 1px solid #ccc;
    font-size: 13px;
    background: #fff;
    cursor: pointer;
  }}

  #img-display {{
    width: 100%;
    max-height: 70vh;
    object-fit: contain;
    display: block;
    border-radius: 10px;
    box-shadow: 0 4px 14px rgba(0,0,0,.12);
    transition: opacity .12s ease-in-out;
  }}
  .caption {{
    text-align: center;
    font-size: 11px;
    color: #999;
    margin-top: 6px;
    margin-bottom: 4px;
  }}

  /* badge indicando se o frame está dentro do loop */
  .badge {{
    display: inline-block;
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 600;
    vertical-align: middle;
  }}
  .badge-loop  {{ background: #ff4b4b22; color: #cc2200; }}
  .badge-fora  {{ background: #88888822; color: #666;    }}
</style>
</head>
<body>

<!-- Barra de info -->
<div class="info-bar">
  <span>📅 <b>{data_label}</b></span>
  <span>🕐 <b id="hora-lbl">--:-- UTC</b></span>
  <span id="badge-lbl"></span>
  <span class="ct" id="frame-lbl"></span>
</div>

<!-- Controles -->
<div class="controls">
  <input type="range" id="slider" min="0" max="{n_total - 1}" value="{n_total - 1}">
  <button class="btn btn-play" id="btn-play">▶ Iniciar</button>
  <button class="btn btn-stop" id="btn-stop">⏹ Parar</button>
  <select id="vel-sel" title="Velocidade da animação">
    <option value="2.0">🐢 Muito lenta</option>
    <option value="1.0">🐌 Lenta</option>
    <option value="0.5" selected>🚶 Normal</option>
    <option value="0.25">🚀 Rápida</option>
    <option value="0.1">⚡ Muito rápida</option>
  </select>
  <button class="btn btn-dl" id="btn-dl" title="Baixar frame atual">⬇</button>
</div>

<!-- Imagem -->
<img id="img-display" src="" alt="GOES Banda-13">
<p class="caption" id="caption"></p>

<script>
  const imagesAll   = {js_images_all};
  const opcoesAll   = {js_opcoes_all};   // todos os horários do dia
  const opcoesLoop  = {js_opcoes_loop};  // janela selecionada para animação
  const dtLabel     = "{data_label}";
  const fmtH        = h => h.slice(0,2) + ':' + h.slice(2) + ' UTC';

  const imgEl    = document.getElementById('img-display');
  const slider   = document.getElementById('slider');
  const horaLbl  = document.getElementById('hora-lbl');
  const frameLbl = document.getElementById('frame-lbl');
  // const badgeLbl = document.getElementById('badge-lbl');
  const caption  = document.getElementById('caption');
  const btnPlay  = document.getElementById('btn-play');
  const btnStop  = document.getElementById('btn-stop');
  const btnDl    = document.getElementById('btn-dl');
  const velSel   = document.getElementById('vel-sel');

  const loopSet  = new Set(opcoesLoop);   // lookup O(1)
  let timer      = null;
  let loopIdx    = 0;   // índice dentro de opcoesLoop (para animação)

  // ── Exibe um frame pelo índice global (opcoesAll) ──────────────────────
  function showFrame(globalIdx) {{
    const key = opcoesAll[globalIdx];
    imgEl.style.opacity = '0';
    requestAnimationFrame(() => {{
      imgEl.src           = imagesAll[key];
      horaLbl.textContent = fmtH(key);
      slider.value        = globalIdx;

      const inLoop = loopSet.has(key);
      badgeLbl.innerHTML  = inLoop
        ? '<span class="badge badge-loop">🔁 no loop</span>'
        : '<span class="badge badge-fora">fora do loop</span>';

      frameLbl.textContent = (globalIdx + 1) + ' / ' + opcoesAll.length
                           + (timer ? '  ▶' : '');
      caption.textContent  = 'GOES • Banda-13 • ' + dtLabel + ' ' + fmtH(key);
    }});
  }}

  imgEl.addEventListener('load',  () => imgEl.style.opacity = '1');
  imgEl.addEventListener('error', () => imgEl.style.opacity = '1');

  // Inicia no frame mais recente
  showFrame(opcoesAll.length - 1);

  // ── Slider manual (navega por TODOS os frames) ─────────────────────────
  slider.addEventListener('input', () => {{
    stopAnim();
    showFrame(parseInt(slider.value));
  }});

  // ── Animação (loop apenas sobre opcoesLoop) ────────────────────────────
  function stopAnim() {{
    if (timer) {{ clearInterval(timer); timer = null; }}
    btnPlay.textContent = '▶ Iniciar';
    const i = parseInt(slider.value);
    frameLbl.textContent = (i + 1) + ' / ' + opcoesAll.length;
  }}

  function startAnim() {{
    stopAnim();
    // Posiciona loopIdx no frame atual, ou no início do loop se estiver fora
    const curKey = opcoesAll[parseInt(slider.value)];
    const li     = opcoesLoop.indexOf(curKey);
    loopIdx      = li >= 0 ? li : 0;

    const ms = parseFloat(velSel.value) * 1000;
    timer = setInterval(() => {{
      loopIdx = (loopIdx + 1) % opcoesLoop.length;
      const globalIdx = opcoesAll.indexOf(opcoesLoop[loopIdx]);
      showFrame(globalIdx);
    }}, ms);
    btnPlay.textContent = '⏸ Pausar';
  }}

  btnPlay.addEventListener('click', () => timer ? stopAnim() : startAnim());
  btnStop.addEventListener('click', stopAnim);
  velSel.addEventListener('change', () => {{ if (timer) startAnim(); }});

  // ── Download do frame atual ────────────────────────────────────────────
  btnDl.addEventListener('click', () => {{
    const key = opcoesAll[parseInt(slider.value)];
    const a   = document.createElement('a');
    a.href    = imagesAll[key];
    a.download= 'GOES_B13_{data_fmt}_' + key + '.png';
    a.click();
  }});
</script>
</body>
</html>
"""

components.html(html, height=950, scrolling=False)
