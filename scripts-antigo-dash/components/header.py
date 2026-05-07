import os
import streamlit.components.v1 as components

from utils.assets import BASE_DIR, load_img_base64

# =========================
# HEADER
# =========================
def render_header():

    logo_path = os.path.join(BASE_DIR, "img", "logo.png")

    logo_base64 = load_img_base64(logo_path)

    components.html(f"""
    <style>

    .custom-header {{
      position: fixed;
      top: 0;
      left: 0;

      z-index: 9999;
      width: 100%;

      background: white;
      border-bottom: 3px solid #1E9B4E;

      margin: 28px 0 28px 0;
      padding: 20px;
      border-radius: 10px;

      display:flex;
      justify-content:space-between;
      align-items:center;

      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
      box-sizing: border-box;

      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    }}

    .custom-header .left {{
      display:flex;
      align-items:center;
      gap:12px;
    }}

    .custom-header .title {{
      font-weight:700;
      font-size:14px;
      line-height: 1.2;
    }}

    .custom-header .subtitle {{
      font-size:11px;
      color:#6B7280;
      line-height: 1.2;
    }}

    .custom-header .right {{
      display:flex;
      align-items:center;
      gap:10px;
    }}

    .status {{
      background:#E7F6EC;
      color:#15753A;
      padding:6px 12px;
      border-radius:20px;
      font-size:12px;
      font-weight:600;
    }}

    .clock {{
      background:#E6F7FA;
      padding:6px 12px;
      border-radius:20px;

      font-size:13px;
      font-weight:600;
      color:#0E6B75;

      min-width: 120px;
      text-align: center;

      display: inline-flex;
      align-items: center;
      justify-content: center;

      white-space: nowrap;
    }}

    </style>

    <div class="custom-header">

        <div class="left">

            <img src="data:image/png;base64,{logo_base64}" height="28"/>

            <div class="titles">
                <div class="title">
                    Dashboard de Monitoramento e Previsão
                </div>

                <div class="subtitle">
                    DIVMET · CRMN — Centro Regional Norte
                </div>
            </div>

        </div>

        <div class="right">

            <div class="status">
                ● SISTEMA ONLINE
            </div>

            <div id="clock" class="clock">
                Carregando...
            </div>

        </div>

    </div>

    <script>

    function atualizarRelogio() {{

        const el = document.getElementById("clock");

        if (!el) return;

        const agora = new Date();

        const hora = agora.toLocaleTimeString("pt-BR", {{
            timeZone: "America/Sao_Paulo",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        }});

        el.textContent = hora + " BRT";
    }}

    setTimeout(() => {{

        atualizarRelogio();

        setInterval(atualizarRelogio, 1000);

    }}, 200);

    </script>

    """, height=100)