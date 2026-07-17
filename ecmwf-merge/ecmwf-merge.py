import json
import os
import base64
import regex as re
import glob
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components

from dashboard_validacao import render_painel_validacao

# =============================================================================
# CONFIGURAÇÃO DOS DIRETÓRIOS
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_IMGS = os.path.join(BASE_DIR, "FIGS_AMZ_PREC")

COLUNAS_MAPPING = {
    "ECMWF_com": {"pasta": "ECMWF", "suffix": "com_nudging"},
    "ECMWF_sem": {"pasta": "ECMWF", "suffix": "sem_nudging"},
    "ICON_com":  {"pasta": "ICON",  "suffix": "com_nudging"},
    "ICON_sem":  {"pasta": "ICON",  "suffix": "sem_nudging"},
}

# =============================================================================
# CARREGAMENTO E INDEXAÇÃO (CRONOLOGIA COMPLETA DE 48 HORAS)
# =============================================================================
def buscar_imagens_mosaico(data_str, ciclo_str):
    # Formata a pasta exata da rodada. Exemplo: "2026051400"
    pasta_rodada_alvo = f"{data_str}{ciclo_str}"

    dados = {}
    todos_timestamps = set()
    todas_opcoes = set()

    # Regex para extrair a data da previsão inteira (Grupo 1) e o horário (Grupo 2) mais a opção (Grupo 3)
    # Exemplo: (2026-05-14)_(06_00)_cmp_(opt_1)_com_nudging.png
    padrao_arquivo = re.compile(r"(\d{4}-\d{2}-\d{2})_(\d{2}_\d{2})_cmp_(opt_\d+)_")

    for col_key, conf in COLUNAS_MAPPING.items():
        caminho_pasta = os.path.join(PATH_IMGS, conf["pasta"], pasta_rodada_alvo)

        if not os.path.isdir(caminho_pasta):
            continue

        arquivos = glob.glob(os.path.join(caminho_pasta, "*.png"))

        for arq in arquivos:
            nome_arquivo = os.path.basename(arq)
            nome_baixo = nome_arquivo.lower()

            if conf["suffix"] in nome_baixo:
                match = padrao_arquivo.search(nome_arquivo)
                if match:
                    data_prev = match.group(1)       # Ex: "2026-05-15"
                    horario_prev = match.group(2)    # Ex: "06_00"
                    opcao = match.group(3)           # Ex: "opt_1"

                    # Cria um timestamp unificado legível e ordenável: "2026-05-15 06:00"
                    timestamp = f"{data_prev} {horario_prev.replace('_', ':')}"

                    todos_timestamps.add(timestamp)
                    todas_opcoes.add(opcao)

                    if timestamp not in dados:
                        dados[timestamp] = {}
                    if col_key not in dados[timestamp]:
                        dados[timestamp][col_key] = {}

                    try:
                        with open(arq, "rb") as f:
                            encoded = base64.b64encode(f.read()).decode("utf-8")
                            dados[timestamp][col_key][opcao] = f"data:image/png;base64,{encoded}"
                    except Exception:
                        continue

    def extrair_numero(opt_str):
        nums = re.findall(r"\d+", opt_str)
        return int(nums[0]) if nums else 0

    lista_opcoes_ordenada = sorted(list(todas_opcoes), key=extrair_numero)
    # Ordena cronologicamente os dias e horas da previsão ("dia 14 00:00" -> "dia 15 06:00" ...)
    lista_timestamps_ordenada = sorted(list(todos_timestamps))

    return dados, lista_timestamps_ordenada, lista_opcoes_ordenada


# =============================================================================
# RENDERIZADOR DO MOSAICO (HTML / TIME-LAPSE ADAPTADO)
# =============================================================================
def render_mosaic_view(data_str, ciclo_str):
    if not data_str:
        st.info("💡 Por favor, digite uma data válida para iniciar (Exemplo: 20260514).")
        return

    # Remove caracteres extras ou espaços que o usuário possa ter digitado
    data_str = data_str.strip()

    dados_mosaico, lista_horarios, linhas_opcoes = buscar_imagens_mosaico(data_str, ciclo_str)

    if not lista_horarios:
        st.error(f"❌ Nenhuma imagem mapeada para a Rodada: {data_str}{ciclo_str}")
        st.info(f"Verifique se o diretório existe e contém imagens válidas: `FIGS_AMZ_PREC/ECMWF/{data_str}{ciclo_str}/`")
        return

    colunas_tabela = list(COLUNAS_MAPPING.keys())

    html_th_colunas = "".join([f"<th>{col.replace('_', ' ').upper()}</th>" for col in colunas_tabela])

    html_linhas_tabela = ""
    for row in linhas_opcoes:
        celulas_td = ""
        for col in colunas_tabela:
            celulas_td += f'<td><div class="img-box"><img id="img_{col}_{row}" src="" alt=""></div></td>'

        row_label = row.replace("_", " ").upper()
        html_linhas_tabela += f"""
        <tr>
            <td class="row-title">{row_label}</td>
            {celulas_td}
        </tr>
        """

    colunas_json = json.dumps(colunas_tabela)
    linhas_json = json.dumps(linhas_opcoes)
    dados_json = json.dumps(dados_mosaico)
    horarios_json = json.dumps(lista_horarios)

    html_component = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: sans-serif; margin: 0; padding: 5px; background: transparent; }}
            .player-bar {{
                display: flex; align-items: center; gap: 15px;
                background: #f8f9fa; padding: 12px; border-radius: 6px;
                margin-bottom: 20px; border: 1px solid #e9ecef;
            }}
            .btn {{
                padding: 8px 18px; font-weight: bold; cursor: pointer;
                background-color: #1E9B4E; color: white; border: none; border-radius: 4px;
            }}
            .btn-stop {{ background-color: #dc3545; }}
            .slider {{ flex-grow: 1; accent-color: #1E9B4E; }}
            .time-text {{ font-size: 16px; font-weight: bold; min-width: 250px; color: #212529; }}

            .matrix-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
            .matrix-table th, .matrix-table td {{ border: 1px solid #dee2e6; text-align: center; padding: 6px; }}
            .matrix-table th {{ background: #f1f3f5; font-size: 13px; padding: 10px; }}

            .row-title {{
                background: #f8f9fa;
                font-weight: bold;
                width: 130px;
                font-size: 13px;
                white-space: nowrap;
            }}

            .img-box {{
                width: 100%; aspect-ratio: 4/3; background: #000;
                border-radius: 4px; display: flex; align-items: center; justify-content: center;
                overflow: hidden;
            }}
            .img-box img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
            .empty-slot {{ color: #6c757d; font-size: 11px; font-style: italic; }}
        </style>
    </head>
    <body>

    <div class="player-bar">
        <button class="btn" id="playBtn">▶ Play</button>
        <button class="btn btn-stop" id="stopBtn">⏹ Stop</button>
        <div class="time-text">Validade: <span id="timeLabel">-</span> UTC</div>
        <input type="range" id="timeSlider" class="slider" min="0" max="{len(lista_horarios) - 1}" value="0">
        <select id="speedSelect" style="padding: 6px; border-radius: 4px;">
            <option value="1000">Lento</option>
            <option value="500" selected>Normal</option>
            <option value="200">Rápido</option>
        </select>
    </div>

    <table class="matrix-table">
        <thead>
            <tr>
                <th style="width: 130px;">Comparações</th>
                {html_th_colunas}
            </tr>
        </thead>
        <tbody>
            {html_linhas_tabela}
        </tbody>
    </table>

    <script>
        const colunas = {colunas_json};
        const linhas = {linhas_json};
        const dados = {dados_json};
        const horarios = {horarios_json};

        const playBtn = document.getElementById('playBtn');
        const stopBtn = document.getElementById('stopBtn');
        const timeSlider = document.getElementById('timeSlider');
        const timeLabel = document.getElementById('timeLabel');
        const speedSelect = document.getElementById('speedSelect');

        let timer = null;

        function atualizarMosaico(index) {{
            if (!horarios.length) return;
            const timestampAtual = horarios[index];

            // Exibe de forma limpa a Data e Hora no painel do player
            timeLabel.innerText = timestampAtual;
            timeSlider.value = index;

            const dadosDoFrame = dados[timestampAtual] || {{}};

            colunas.forEach(col => {{
                linhas.forEach(row => {{
                    const img = document.getElementById(`img_${{col}}_${{row}}`);
                    const pai = img.parentElement;

                    if (dadosDoFrame[col] && dadosDoFrame[col][row]) {{
                        img.src = dadosDoFrame[col][row];
                        img.style.display = "block";
                        const aviso = pai.querySelector('.empty-slot');
                        if(aviso) aviso.remove();
                    }} else {{
                        img.src = "";
                        img.style.display = "none";
                        if(!pai.querySelector('.empty-slot')) {{
                            pai.insertAdjacentHTML('beforeend', '<div class="empty-slot">Sem Dado</div>');
                        }}
                    }}
                }});
            }});
        }}

        function stop() {{
            if (timer) {{ clearInterval(timer); timer = null; }}
        }}

        function play() {{
            stop();
            let idx = parseInt(timeSlider.value);
            timer = setInterval(() => {{
                idx = (idx + 1) % horarios.length;
                atualizarMosaico(idx);
            }}, parseInt(speedSelect.value));
        }}

        playBtn.onclick = play;
        stopBtn.onclick = stop;
        timeSlider.oninput = () => {{ stop(); atualizarMosaico(parseInt(timeSlider.value)); }};
        speedSelect.onchange = () => {{ if (timer) play(); }};

        // Inicia no primeiro frame (ex: 00h da previsão)
        atualizarMosaico(0);
    </script>
    </body>
    </html>
    """

    altura_container = (len(linhas_opcoes) * 245) + 120
    components.html(html_component, height=altura_container, scrolling=True)


# =============================================================================
# ABA 1: MOSAICO (inputs + player + tabela)
# =============================================================================
def render_aba_mosaico():
    col_data, col_ciclo = st.columns([3, 1])

    with col_data:
        data_input = st.text_input(
            "Digite a Data (Padrão: AAAAMMDD)",
            value="20260514",
            key="mosaico_data_input",
        )

    with col_ciclo:
        ciclo_input = st.selectbox(
            "Ciclo",
            options=["00", "12"],
            index=0,
            key="mosaico_ciclo_input",
        )

    render_mosaic_view(data_input, ciclo_input)


# =============================================================================
# INTERFACE PRINCIPAL
# =============================================================================
if __name__ == "__main__":
    st.set_page_config(layout="wide", page_title="Mosaico Clima - AMZ")
    st.title("Mosaico de Modelos Meteorológicos")

    aba_mosaico, aba_validacao = st.tabs(["🗺️ Mosaico de Rodadas", "📊 Validação Científica"])

    with aba_mosaico:
        render_aba_mosaico()

    with aba_validacao:
        render_painel_validacao()