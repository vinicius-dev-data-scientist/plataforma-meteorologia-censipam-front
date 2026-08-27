import calendar
import os
from datetime import datetime
import pandas as pd
import xarray as xr
import sys

# Corrige os caminhos do ecCodes no Anaconda/Windows
conda_env_path = sys.prefix
eccodes_def = os.path.join(conda_env_path, "Library", "share", "eccodes", "definitions")

if os.path.exists(eccodes_def):
    os.environ["ECCODES_DEFINITION_PATH"] = eccodes_def


def obter_dias_do_mes(ano: int, mes: int) -> list:
    """Retorna uma lista de strings no formato YYYYMMDD para todos os dias do mês informado."""
    num_dias = calendar.monthrange(ano, mes)[1]
    return [f"{ano}{mes:02d}{dia:02d}" for dia in range(1, num_dias + 1)]


def carregar_acumulado_observado(
    ano: int, mes: int, base_dir: str = "datasets/gribs"
) -> xr.Dataset:
    """Lê os arquivos GRIB2 do mês/ano, verifica a integridade do período e

    retorna o acumulado mensal (dados do Observado).
    """
    dias_esperados = obter_dias_do_mes(ano, mes)
    pasta_mes = os.path.join(base_dir, str(ano), f"{mes:02d}")

    if not os.path.exists(pasta_mes):
        raise FileNotFoundError(
            f"Diretório do mês não encontrado: {pasta_mes}"
        )

    # Constrói os caminhos esperados para os arquivos .grib2
    arquivos_esperados = [
        os.path.join(pasta_mes, f"MERGE_CPTEC_{data_str}.grib2")
        for data_str in dias_esperados
    ]

    # Validação condicional da existência e integridade de todos os dias do período
    arquivos_existentes = [f for f in arquivos_esperados if os.path.isfile(f)]
    dias_faltantes = len(arquivos_esperados) - len(arquivos_existentes)

    if dias_faltantes > 0:
        faltantes_nomes = set(arquivos_esperados) - set(arquivos_existentes)
        print(
            f"⚠️ AVISO: O período {mes:02d}/{ano} está incompleto. Faltam {dias_faltantes} arquivo(s):"
        )
        for f in sorted(faltantes_nomes):
            print(f"  - {os.path.basename(f)}")
        if not arquivos_existentes:
            raise ValueError(
                f"Nenhum arquivo válido encontrado em {pasta_mes}."
            )

    print(
        f"📂 Carregando {len(arquivos_existentes)} arquivo(s) GRIB2 de {pasta_mes}..."
    )

    # Leitura e concatenação via xarray
    # Usando o engine cfgrib padrão para leitura de GRIB/GRIB2
    # Leitura e concatenação via xarray com correções para GRIB2/ecCodes
    ds = xr.open_mfdataset(
        arquivos_existentes,
        engine="cfgrib",
        combine="nested",
        concat_dim="time",
        parallel=False,  # Desativado no Windows para evitar conflito de leitura concorrente
        backend_kwargs={
            "filter_by_keys": {"typeOfLevel": "surface"},
            "indexpath": ""  # Processa o índice na memória RAM e ignora geração de arquivos .idx
        }
    )

    # Processamento para gerar o acumulado do mês (Observado)
    ds_acumulado = ds.sum(dim="time", keep_attrs=True)

    return ds_acumulado

def filtrar_por_escala(ds, escala, numero_periodo=1):
    """
    Filtra o Dataset xarray de acordo com a escala temporal e sub-período selecionado.
    """
    if escala == "Decêndio":
        # 1º Decêndio (1-10), 2º (11-20), 3º (21 ao fim)
        limites = [(1, 10), (11, 20), (21, 31)]
        d_ini, d_fim = limites[numero_periodo - 1]
        return ds.sel(time=(ds.time.dt.day >= d_ini) & (ds.time.dt.day <= d_fim))
        
    elif escala == "Quinzena":
        # 1ª Quinzena (1-15), 2ª (16 ao fim)
        limites = [(1, 15), (16, 31)]
        q_ini, q_fim = limites[numero_periodo - 1]
        return ds.sel(time=(ds.time.dt.day >= q_ini) & (ds.time.dt.day <= q_fim))
        
    return ds  # Retorna o mês completo sem fatiar


if __name__ == "__main__":
    # Exemplo de execução para Janeiro/2025 conforme arquitetura apresentada
    ANO_ALVO = 2025
    MES_ALVO = 1

    try:
        ds_observado = carregar_acumulado_observado(ANO_ALVO, MES_ALVO)
        print("\n✅ Processamento do Observado concluído com sucesso!")
        print(ds_observado)
    except Exception as e:
        print(f"\n❌ Erro no processamento: {e}")