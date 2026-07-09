# validacao_precip.py

import xarray as xr
import numpy as np

def processar_validacao(caminho_merge_grib, caminho_ecmwf_nc):
    """
    Lê o GRIB2 do MERGE, o NetCDF do ECMWF global, realiza o regradeamento geométrico
    limpo e calcula o erro médio quadrático (RMSE).
    """
    print("🛰️ Carregando dados do MERGE (GRIB2)...")
    ds_merge = xr.open_dataset(caminho_merge_grib, engine='cfgrib')
    var_merge = list(ds_merge.data_vars)[0]
    da_merge = ds_merge[var_merge]

    # Garante que as coordenadas de longitude do MERGE estejam de -180 a 180
    if da_merge.longitude.max() > 180:
        da_merge = da_merge.assign_coords(longitude=(((da_merge.longitude + 180) % 360) - 180))
    da_merge = da_merge.sortby('longitude')

    print("🇪🇺 Carregando dados do ECMWF (NetCDF)...")
    ds_ecmwf = xr.open_dataset(caminho_ecmwf_nc)
    
    var_ecmwf = 'tp' if 'tp' in ds_ecmwf.data_vars else list(ds_ecmwf.data_vars)[0]
    da_ecmwf = ds_ecmwf[var_ecmwf]

    # Padroniza os nomes de coordenadas do ECMWF para bater com o MERGE
    renomear = {}
    if 'lat' in da_ecmwf.dims: renomear['lat'] = 'latitude'
    if 'lon' in da_ecmwf.dims: renomear['lon'] = 'longitude'
    if renomear:
        da_ecmwf = da_ecmwf.rename(renomear)

    # Converte a longitude do ECMWF de (0 a 360) para (-180 a 180)
    if da_ecmwf.longitude.max() > 180:
        da_ecmwf = da_ecmwf.assign_coords(longitude=(((da_ecmwf.longitude + 180) % 360) - 180))
    da_ecmwf = da_ecmwf.sortby('longitude')
    da_ecmwf = da_ecmwf.sortby('latitude')

    # Remove qualquer dimensão de tempo ou step antes de interpolar para evitar conflito de índices
    da_ecmwf_2d = da_ecmwf.squeeze()
    if len(da_ecmwf_2d.dims) > 2:
        # Se ainda sobrarem dimensões extras (como valid_time), seleciona apenas a primeira fatia
        da_ecmwf_2d = da_ecmwf_2d.isel({d: 0 for d in da_ecmwf_2d.dims if d not in ['latitude', 'longitude']})

    print("🧮 Executando o Regradeamento espacial...")
    # Interpola ignorando coordenadas de tempo associadas
    ecmwf_regradeado = da_ecmwf_2d.interp(
        latitude=da_merge.latitude,
        longitude=da_merge.longitude,
        method='linear'
    )

    # Extração final das matrizes numéricas em formato NumPy puro
    valores_merge = da_merge.values
    valores_ecmwf = ecmwf_regradeado.values

    # Correção de escala: Se o ECMWF estiver em metros e o MERGE em milímetros
    if np.nanmax(valores_ecmwf) < 1.0 and np.nanmax(valores_merge) > 1.0:
        print("📏 Convertendo unidade do ECMWF de metros para milímetros...")
        valores_ecmwf = valores_ecmwf * 1000.0

    print("📊 Calculando métricas...")
    # Converte tudo para vetores 1D lineares para blindar o cálculo contra erros de dimensões
    vetor_merge = valores_merge.ravel()
    vetor_ecmwf = valores_ecmwf.ravel()

    # Cria a máscara booleana livre de erros de indexação
    mascara = ~np.isnan(vetor_merge) & ~np.isnan(vetor_ecmwf)
    
    erro_quadratico = (vetor_merge[mascara] - vetor_ecmwf[mascara]) ** 2
    rmse = np.sqrt(np.mean(erro_quadratico))
    
    print(f"✅ Sucesso! RMSE Calculado: {rmse:.4f} mm")
    return float(rmse)

if __name__ == "__main__":
    ARQUIVO_MERGE = "dados/MERGE_CPTEC_2026060100.grib2"
    ARQUIVO_ECMWF = "dados/dd19735e1a81a17da86a9589ac5d1bfa.nc" 
    
    try:
        rmse_resultado = processar_validacao(ARQUIVO_MERGE, ARQUIVO_ECMWF)
    except Exception as e:
        print(f"❌ Erro ao processar os arquivos: {e}")
        
if __name__ == "__main__":
    # 1. Defina o arquivo observado do MERGE
    ARQUIVO_MERGE = "dados/MERGE_CPTEC_2026060100.grib2"
    
    # 2. Defina os dois arquivos das suas simulações do ECMWF
    ARQUIVO_SIMULACAO_A = "dados/dd19735e1a81a17da86a9589ac5d1bfa.nc" # Ex: Com Nudging
    ARQUIVO_SIMULACAO_B = "dados/6b1b424d99bfc6fab01a0390722e15c1.nc" # Ex: Sem Nudging
    
    print("==================================================")
    print("📊 INICIANDO COMPARAÇÃO INTERNA DE SIMULAÇÕES")
    print("==================================================")
    
    try:
        print("\n[Rodada A]")
        rmse_a = processar_validacao(ARQUIVO_MERGE, ARQUIVO_SIMULACAO_A)
        
        print("\n[Rodada B]")
        rmse_b = processar_validacao(ARQUIVO_MERGE, ARQUIVO_SIMULACAO_B)
        
        print("\n=================== VEREDITO ===================")
        if rmse_a < rmse_b:
            print(f"🏆 A Simulação A ({ARQUIVO_SIMULACAO_A}) foi MELHOR!")
            print(f"Desvio médio menor: {rmse_a:.4f} mm contra {rmse_b:.4f} mm da Simulação B.")
        elif rmse_b < rmse_a:
            print(f"🏆 A Simulação B ({ARQUIVO_SIMULACAO_B}) foi MELHOR!")
            print(f"Desvio médio menor: {rmse_b:.4f} mm contra {rmse_a:.4f} mm da Simulação A.")
        else:
            print("⚖️ Ambas as simulações tiveram exatamente o mesmo desempenho.")
        print("==================================================")
        
    except Exception as e:
        print(f"\n❌ Erro ao processar o comparativo: {e}")

# Parte Visual do Streamlit

import streamlit as st

st.title("🛰️ Central de Validação Meteorológica")
st.markdown("---")

# Seus cálculos rodam em segundo plano e geram as variáveis rmse_a e rmse_b
rmse_a = 0.8286
rmse_b = 1.0399

st.subheader("🏆 Veredito Estatístico da Rodada")

col1, col2 = st.columns(2)

with col1:
    # Como menor erro é melhor, calculamos a melhora percentual ou absoluta
    delta_a = f"-{rmse_b - rmse_a:.4f} mm (Mais Preciso)"
    st.metric(
        label="Simulação A (Com Nudging)", 
        value=f"{rmse_a:.4f} mm", 
        delta=delta_a,
        delta_color="inverse" # Deixa verde porque o valor menor é positivo para nós
    )

with col2:
    st.metric(
        label="Simulação B (Sem Nudging)", 
        value=f"{rmse_b:.4f} mm", 
        delta=f"+{rmse_b - rmse_a:.4f} mm (Maior Desvio)",
        delta_color="normal" # Deixa vermelho/normal indicando maior erro
    )

st.success(f"**Análise Concluída:** A Simulação A reduziu o erro médio quadrático em **{((rmse_b - rmse_a)/rmse_b)*100:.1f}%** em comparação com a Simulação B, sendo a recomendada para inicializar o próximo ciclo de previsão.")