import xarray as xr
import numpy as np
from scipy.interpolate import RegularGridInterpolator

def regradear_e_calcular_rmse(caminho_merge_nc, caminho_ecmwf_nc):
    """
    Carrega os dados brutos NetCDF, faz o regradeamento do ECMWF 
    para a grade do MERGE e calcula o RMSE espacial.
    """
    # 1. Carrega os datasets brutos
    ds_merge = xr.open_dataset(caminho_merge_nc)
    ds_ecmwf = xr.open_dataset(caminho_ecmwf_nc)
    
    # Extrai as coordenadas do MERGE (nossa grade alvo)
    lat_alvo = ds_merge['lat'].values
    lon_alvo = ds_merge['lon'].values
    precip_merge = ds_merge['precip'].values # Matriz observada
    
    # Extrai as coordenadas originais do ECMWF
    lat_orig = ds_ecmwf['latitude'].values
    lon_orig = ds_ecmwf['longitude'].values
    precip_ecmwf = ds_ecmwf['tp'].values # Matriz prevista original
    
    # Como as latitudes do ECMWF às vezes vêm invertidas (90 a -90), garantimos a ordenação
    if lat_orig[0] > lat_orig[-1]:
        lat_orig = lat_orig[::-1]
        precip_ecmwf = np.flip(precip_ecmwf, axis=0)
        
    # 2. Cria o interpolador com a grade original do ECMWF
    interpolador = RegularGridInterpolator(
        (lat_orig, lon_orig), 
        precip_ecmwf, 
        bounds_error=False, 
        fill_value=0.0
    )
    
    # 3. Faz o Regradeamento (regrid) projetando a grade do MERGE
    mesh_lat, mesh_lon = np.meshgrid(lat_alvo, lon_alvo, indexing='ij')
    pontos_alvo = np.array([mesh_lat.ravel(), mesh_lon.ravel()]).T
    
    # ECMWF regradeado com as mesmas dimensões exatas do MERGE
    ecmwf_regradeado = interpolador(pontos_alvo).reshape(mesh_lat.shape)
    
    # 4. Calcula a métrica de erro (RMSE) descartando possíveis valores nulos (NaN)
    mascara = ~np.isnan(precip_merge) & ~np.isnan(ecmwf_regradeado)
    erro_quadratico = (precip_merge[mascara] - ecmwf_regradeado[mascara]) ** 2
    rmse = np.sqrt(np.mean(erro_quadratico))
    
    # Retorna o valor de erro e a matriz regradeada caso queira plotar futuramente
    return float(rmse), ecmwf_regradeado