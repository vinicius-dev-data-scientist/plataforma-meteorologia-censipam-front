# mosaic_view.py

import json
import os
import base64
import regex as re
import glob
import streamlit as st
import streamlit.components.v1 as components

# =============================================================================
# DEFINIÇÃO DA BASE DE DIRETÓRIOS
# =============================================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATH_IMGS = os.path.join(BASE_DIR, "img", "Figuras")

# =============================================================================
# CARREGAMENTO DINÂMICO SEGUINDO A HIERARQUIA (Ano/Mês/Dia)
# =============================================================================
@st.cache_data(show_spinner="📡 Indexando mosaico de opções...")
def buscar_imagens_hierarquia(data_selecionada):
    """
    Busca as imagens diretamente na estrutura de pastas:
    PATH_IMGS / Clima / Ano / Mês / Dia
    """
    ano = data_selecionada.strftime("%Y")
    mes = data_selecionada.strftime("%m")
    dia = data_selecionada.strftime("%d")
    
    pasta = os.path.join(PATH_IMGS, "Clima", ano, mes, dia)
    
    if not os.path.exists(pasta):
        return {}, []
    
    arquivos = glob.glob(os.path.join(pasta, "*.png"))
    
    dados = {}
    todos_horarios = set()
    
    # Regex para capturar: Horário (HH_MM), a Opção (opt_X)
    padrao = re.compile(r"_(\d{2}_\d{2})_cmp_(opt_\d+)_")
    
    for arq in arquivos:
        nome_arquivo = os.path.basename(arq)
        match = padrao.search(nome_arquivo)
        
        if match:
            horario_prev = match.group(1) # ex: "06_00"
            opcao = match.group(2)        # ex: "opt_1"
            
            nome_baixo = nome_arquivo.lower()
            if "ecmwf" in nome_baixo or "ecm" in nome_baixo:
                coluna = "ECMWF_com" if "com" in nome_baixo else "ECMWF_sem"
            elif "icon" in nome_baixo:
                coluna = "ICON_com" if "com" in nome_baixo else "ICON_sem"
            else:
                coluna = "ECMWF_com" if "com_nudging" in nome_baixo else "ECMWF_sem"
            
            todos_horarios.add(horario_prev)
            
            if horario_prev not in dados:
                dados[horario_prev] = {}
            if coluna not in dados[horario_prev]:
                dados[horario_prev][coluna] = {}
                
            try:
                with open(arq, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("utf-8")
                    dados[horario_prev][coluna][opcao] = f"data:image/png;base64,{encoded}"
            except Exception:
                continue
                
    return dados, sorted(list(todos_horarios))


# =============================================================================
# RENDERIZADOR DO MOSAICO
# =============================================================================
def render_mosaic_view(config):
    """
    Exibe a matriz completa com todas as opções (opt_1 até opt_193)
    e o slider de lapso temporal controlando o horário da previsão.
    """
    data_inicio = config.get("data_inicio")
    
    dados_mosaico, lista_horarios = buscar_imagens_hierarquia(data_inicio)
    
    if not lista_horarios:
        st.warning(f"Nenhuma imagem encontrada na pasta Clima para o dia: {data_inicio.strftime('%d/%m/%Y')}")
        return

    colunas_tabela = ["ECMWF_com", "ECMWF_sem", "ICON_com", "ICON_sem"]
    
    # Lista estendida contendo as opções conforme solicitado
    linhas_opcoes = [
        "opt_1", "opt_2", "opt_3", "opt_5", "opt_6", "opt_10", 
        "opt_16", "opt_93", "opt_193"
    ]

    # Correção dos erros de sintaxe gerando os blocos HTML fora da f-string principal
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

    # Conversão limpa para JSON seguro
    colunas_json = json.dumps(colunas_tabela)
    linhas_json = json.dumps(linhas_opcoes)
    dados_json = json.dumps(dados_mosaico)
    horarios_json = json.dumps(lista_horarios)

    # Injeção segura do template HTML com as variáveis já resolvidas e pré-calculadas
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
            .time-text {{ font-size: 16px; font-weight: bold; min-width: 140px; }}
            
            .matrix-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
            .matrix-table th, .matrix-table td {{ border: 1px solid #dee2e6; text-align: center; padding: 8px; }}
            .matrix-table th {{ background: #f1f3f5; font-size: 14px; padding: 10px; }}
            .row-title {{ background: #f8f9fa; font-weight: bold; width: 100px; font-size: 13px; }}
            
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
        <div class="time-text">Previsão: <span id="timeLabel">-</span></div>
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
                <th>Comparações</th>
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
            const horaAtual = horarios[index];
            timeLabel.innerText = horaAtual.replace("_", ":") + " UTC";
            timeSlider.value = index;

            const dadosDoFrame = dados[horaAtual] || {{}};

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

        atualizarMosaico(0);
    </script>
    </body>
    </html>
    """

    altura_container = (len(linhas_opcoes) * 220) + 120
    components.html(html_component, height=altura_container, scrolling=True)