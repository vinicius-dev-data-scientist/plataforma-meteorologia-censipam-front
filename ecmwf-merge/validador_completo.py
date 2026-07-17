# validador_completo.py
"""
Validação científica MERGE (observado) x ECMWF (simulado) — versão completa.

Funcionalidades:
- Lê os 24 GRIB2 horários do MERGE de um dia (dados/MERGE_CPTEC_AAAAMMDDHH.grib2)
- Lê o(s) NetCDF(s) do ECMWF (podem ter dimensão de tempo 'valid_time'/'time'/'step')
- Regradeamento geométrico (interp_like) do ECMWF para a grade do MERGE
- Calcula métricas contínuas (RMSE, MAE, Bias, Correlação de Pearson, SSIM)
- Calcula métricas de evento binário / contingência (POD, FAR, CSI, ETS, FBI)
- Roda a validação hora a hora, casando cada MERGE_HH.grib2 com o instante mais
  próximo no NetCDF do ECMWF (tolerância configurável)
- Compara N simulações (ex: Com Nudging x Sem Nudging) e monta um DataFrame
  "longo" pronto para plotar
- Salva o resultado em JSON (cache) para o dashboard Streamlit não recalcular
  toda vez que a página recarrega

Uso rápido (linha de comando):
    python validador_completo.py

Uso programático:
    from validador_completo import validar_dia_comparativo
    df = validar_dia_comparativo(
        pasta_merge="dados",
        data_str="20260601",
        simulacoes={"Com Nudging": "dados/dd19735e1a81a17da86a9589ac5d1bfa.nc",
                    "Sem Nudging": "dados/6b1b424d99bfc6fab01a0390722e15c1.nc"},
        salvar_json="dados/validacao_cache.json",
    )
"""

import glob
import json
import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import xarray as xr

try:
    from skimage.metrics import structural_similarity as ssim_func
    _TEM_SKIMAGE = True
except ImportError:
    _TEM_SKIMAGE = False


# =============================================================================
# LEITURA E PADRONIZAÇÃO DE GRADES
# =============================================================================
def _padronizar_lon(da):
    """Converte longitude de 0..360 para -180..180 e reordena."""
    if float(da.longitude.max()) > 180:
        da = da.assign_coords(longitude=(((da.longitude + 180) % 360) - 180))
        da = da.sortby("longitude")
    return da


def carregar_merge(caminho_grib2):
    """Abre um arquivo horário do MERGE e retorna um DataArray 2D (lat, lon)."""
    ds = xr.open_dataset(caminho_grib2, engine="cfgrib")
    var = list(ds.data_vars)[0]
    da = ds[var]
    if len(da.dims) > 2:
        da = da.squeeze()
    da = _padronizar_lon(da)
    da = da.sortby("latitude")
    return da


def carregar_ecmwf(caminho_nc):
    """
    Abre o NetCDF do ECMWF e retorna um DataArray que preserva a dimensão de
    tempo (renomeada para 'valid_time'), já com lat/lon padronizados.
    """
    ds = xr.open_dataset(caminho_nc)
    var = "tp" if "tp" in ds.data_vars else list(ds.data_vars)[0]
    da = ds[var]

    renomear = {}
    if "lat" in da.dims:
        renomear["lat"] = "latitude"
    if "lon" in da.dims:
        renomear["lon"] = "longitude"
    if renomear:
        da = da.rename(renomear)

    # Unifica o nome da dimensão temporal (varia entre 'time', 'valid_time', 'step')
    for cand in ("valid_time", "time"):
        if cand in da.dims:
            if cand != "valid_time":
                da = da.rename({cand: "valid_time"})
            break

    da = _padronizar_lon(da)
    da = da.sortby("longitude").sortby("latitude")
    return da


def _selecionar_horario_mais_proximo(da_ecmwf, timestamp_alvo, tolerancia_min=90):
    """Seleciona a fatia 2D do ECMWF cujo valid_time é mais próximo do alvo."""
    if "valid_time" not in da_ecmwf.dims:
        # já é 2D, sem dimensão temporal
        return da_ecmwf, None

    tempos = pd.to_datetime(da_ecmwf.valid_time.values)
    alvo = pd.Timestamp(timestamp_alvo)
    diffs = np.abs(tempos - alvo)
    idx_mais_proximo = int(np.argmin(diffs))
    delta_min = diffs[idx_mais_proximo].total_seconds() / 60.0

    if delta_min > tolerancia_min:
        return None, delta_min

    fatia = da_ecmwf.isel(valid_time=idx_mais_proximo)
    if len(fatia.dims) > 2:
        fatia = fatia.squeeze()
    return fatia, delta_min


# =============================================================================
# REGRADEAMENTO
# =============================================================================
def regradear(da_ecmwf_2d, da_merge_alvo):
    """Interpola o ECMWF (2D) para a grade exata do MERGE."""
    regradeado = da_ecmwf_2d.interp_like(da_merge_alvo, method="linear")
    if len(regradeado.dims) > 2:
        regradeado = regradeado.squeeze()
    return regradeado


def _corrigir_escala(vetor_obs, vetor_sim):
    """Se o ECMWF vier em metros (ERA5 padrão) e o MERGE em mm, converte."""
    if np.nanmax(vetor_sim) < 1.0 and np.nanmax(vetor_obs) > 1.0:
        vetor_sim = vetor_sim * 1000.0
    return vetor_sim


# =============================================================================
# MÉTRICAS CONTÍNUAS
# =============================================================================
def metricas_continuas(obs_2d, sim_2d):
    """RMSE, MAE, Bias médio e Correlação de Pearson, calculados na área comum."""
    vetor_obs = np.asarray(obs_2d).ravel()
    vetor_sim = np.asarray(sim_2d).ravel()
    vetor_sim = _corrigir_escala(vetor_obs, vetor_sim)

    mascara = ~np.isnan(vetor_obs) & ~np.isnan(vetor_sim)
    o = vetor_obs[mascara]
    s = vetor_sim[mascara]

    if o.size == 0:
        return {"rmse": np.nan, "mae": np.nan, "bias": np.nan, "pearson": np.nan, "n_pontos": 0}

    rmse = float(np.sqrt(np.mean((o - s) ** 2)))
    mae = float(np.mean(np.abs(o - s)))
    bias = float(np.mean(s - o))
    pearson = float(np.corrcoef(o, s)[0, 1]) if o.size > 1 and np.std(o) > 0 and np.std(s) > 0 else np.nan

    return {"rmse": rmse, "mae": mae, "bias": bias, "pearson": pearson, "n_pontos": int(o.size)}


def metrica_ssim(obs_2d, sim_2d):
    """Similaridade estrutural (0 a 1) entre os dois campos de chuva."""
    if not _TEM_SKIMAGE:
        return np.nan

    obs = np.asarray(obs_2d, dtype=float)
    sim = np.asarray(sim_2d, dtype=float)
    sim = _corrigir_escala(obs.ravel(), sim.ravel()).reshape(sim.shape)

    obs = np.nan_to_num(obs, nan=0.0)
    sim = np.nan_to_num(sim, nan=0.0)

    valor_max = max(np.nanmax(obs), np.nanmax(sim), 1e-6)
    try:
        valor = ssim_func(obs, sim, data_range=valor_max)
        return float(valor)
    except Exception:
        return np.nan


# =============================================================================
# MÉTRICAS CATEGÓRICAS (TABELA DE CONTINGÊNCIA)
# =============================================================================
def metricas_categoricas(obs_2d, sim_2d, limiar_mm=1.0):
    """
    Binariza os campos (chuva >= limiar_mm vira evento) e calcula:
    POD  - Probability of Detection (taxa de acerto do que choveu)
    FAR  - False Alarm Ratio (taxa de alarme falso)
    CSI  - Critical Success Index
    ETS  - Equitable Threat Score (acerto descontando o acaso)
    FBI  - Frequency Bias Index (super/subestimação de área de chuva)
    """
    vetor_obs = np.asarray(obs_2d).ravel()
    vetor_sim = np.asarray(sim_2d).ravel()
    vetor_sim = _corrigir_escala(vetor_obs, vetor_sim)

    mascara = ~np.isnan(vetor_obs) & ~np.isnan(vetor_sim)
    o = vetor_obs[mascara] >= limiar_mm
    s = vetor_sim[mascara] >= limiar_mm

    if o.size == 0:
        chaves = ["pod", "far", "csi", "ets", "fbi"]
        return {k: np.nan for k in chaves}

    hits = int(np.sum(o & s))                 # acertou que choveu
    misses = int(np.sum(o & ~s))               # choveu e o modelo não previu
    false_alarms = int(np.sum(~o & s))         # modelo previu chuva que não ocorreu
    correct_neg = int(np.sum(~o & ~s))         # acertou que não choveu
    n = hits + misses + false_alarms + correct_neg

    pod = hits / (hits + misses) if (hits + misses) > 0 else np.nan
    far = false_alarms / (hits + false_alarms) if (hits + false_alarms) > 0 else np.nan
    csi = hits / (hits + misses + false_alarms) if (hits + misses + false_alarms) > 0 else np.nan
    fbi = (hits + false_alarms) / (hits + misses) if (hits + misses) > 0 else np.nan

    hits_acaso = ((hits + misses) * (hits + false_alarms)) / n if n > 0 else 0
    denom_ets = (hits + misses + false_alarms - hits_acaso)
    ets = (hits - hits_acaso) / denom_ets if denom_ets > 0 else np.nan

    return {
        "pod": float(pod) if pod == pod else np.nan,
        "far": float(far) if far == far else np.nan,
        "csi": float(csi) if csi == csi else np.nan,
        "ets": float(ets) if ets == ets else np.nan,
        "fbi": float(fbi) if fbi == fbi else np.nan,
    }


# =============================================================================
# VALIDAÇÃO DE UMA ÚNICA HORA (uma simulação x um horário do MERGE)
# =============================================================================
def validar_par(caminho_merge_grib2, da_ecmwf_completo, timestamp_alvo, limiar_mm=1.0):
    """Retorna um dict com todas as métricas para um horário específico."""
    da_merge = carregar_merge(caminho_merge_grib2)

    fatia_ecmwf, delta_min = _selecionar_horario_mais_proximo(da_ecmwf_completo, timestamp_alvo)
    if fatia_ecmwf is None:
        return None

    ecmwf_regrid = regradear(fatia_ecmwf, da_merge)

    obs = da_merge.values
    sim = ecmwf_regrid.values

    resultado = {}
    resultado.update(metricas_continuas(obs, sim))
    resultado.update(metricas_categoricas(obs, sim, limiar_mm=limiar_mm))
    resultado["ssim"] = metrica_ssim(obs, sim)
    resultado["defasagem_min"] = None if delta_min is None else round(float(delta_min), 1)
    return resultado


# =============================================================================
# VALIDAÇÃO DO DIA INTEIRO, MULTI-SIMULAÇÃO
# =============================================================================
def _listar_arquivos_merge_do_dia(pasta_merge, data_str):
    """Encontra os arquivos MERGE_CPTEC_AAAAMMDDHH.grib2 de um dia e extrai o horário."""
    padrao = os.path.join(pasta_merge, f"MERGE_CPTEC_{data_str}*.grib2")
    arquivos = sorted(glob.glob(padrao))
    itens = []
    for caminho in arquivos:
        nome = os.path.basename(caminho)
        # MERGE_CPTEC_2026060100.grib2 -> AAAAMMDDHH = nome[13:23]
        try:
            aaaammddhh = nome.replace("MERGE_CPTEC_", "").replace(".grib2", "")
            timestamp = datetime.strptime(aaaammddhh, "%Y%m%d%H")
            itens.append((caminho, timestamp))
        except ValueError:
            continue
    return itens


def validar_dia_comparativo(pasta_merge, data_str, simulacoes, limiar_mm=1.0,
                             salvar_json=None, progresso_callback=None):
    """
    Roda a validação para todas as horas do dia `data_str` (AAAAMMDD) contra
    cada simulação em `simulacoes` (dict {rotulo: caminho_do_nc}).

    Retorna um DataFrame "longo": uma linha por (horário, simulação).
    """
    arquivos_merge = _listar_arquivos_merge_do_dia(pasta_merge, data_str)
    if not arquivos_merge:
        raise FileNotFoundError(
            f"Nenhum arquivo MERGE_CPTEC_{data_str}HH.grib2 encontrado em '{pasta_merge}'."
        )

    das_ecmwf = {rotulo: carregar_ecmwf(caminho) for rotulo, caminho in simulacoes.items()}

    linhas = []
    total_passos = len(arquivos_merge) * len(simulacoes)
    passo_atual = 0

    for caminho_merge, timestamp in arquivos_merge:
        for rotulo, da_ecmwf in das_ecmwf.items():
            passo_atual += 1
            if progresso_callback:
                progresso_callback(passo_atual, total_passos, f"{timestamp:%H:%M} — {rotulo}")
            try:
                metricas = validar_par(caminho_merge, da_ecmwf, timestamp, limiar_mm=limiar_mm)
            except Exception as erro:
                metricas = None
                erro_msg = str(erro)
            else:
                erro_msg = None

            linha = {
                "data": data_str,
                "horario": timestamp.strftime("%H:%M"),
                "timestamp": timestamp.isoformat(),
                "simulacao": rotulo,
                "arquivo_merge": os.path.basename(caminho_merge),
            }
            if metricas is not None:
                linha.update(metricas)
                linha["status"] = "ok"
            else:
                linha["status"] = f"falhou: {erro_msg}" if erro_msg else "sem par temporal dentro da tolerância"
            linhas.append(linha)

    df = pd.DataFrame(linhas)

    if salvar_json:
        os.makedirs(os.path.dirname(salvar_json), exist_ok=True) if os.path.dirname(salvar_json) else None
        df.to_json(salvar_json, orient="records", indent=2, force_ascii=False)

    return df


def carregar_cache(caminho_json):
    """Lê de volta o DataFrame salvo por validar_dia_comparativo."""
    if not os.path.exists(caminho_json):
        return None
    return pd.read_json(caminho_json, orient="records")


def resumo_veredito(df):
    """
    Recebe o DataFrame longo e devolve um DataFrame curto com a média de cada
    métrica por simulação, mais uma coluna 'melhor' apontando o vencedor por
    métrica (considerando que RMSE/MAE/FAR menor é melhor, e SSIM/POD/CSI/ETS
    maior é melhor; FBI ideal é o mais próximo de 1).
    """
    ok = df[df["status"] == "ok"].copy()
    if ok.empty:
        return pd.DataFrame()

    agrupado = ok.groupby("simulacao").agg(
        rmse_medio=("rmse", "mean"),
        mae_medio=("mae", "mean"),
        bias_medio=("bias", "mean"),
        pearson_medio=("pearson", "mean"),
        ssim_medio=("ssim", "mean"),
        pod_medio=("pod", "mean"),
        far_medio=("far", "mean"),
        csi_medio=("csi", "mean"),
        ets_medio=("ets", "mean"),
        fbi_medio=("fbi", "mean"),
        horas_validadas=("horario", "count"),
    ).reset_index()

    return agrupado.sort_values("rmse_medio")


# =============================================================================
# EXECUÇÃO DIRETA
# =============================================================================
if __name__ == "__main__":
    PASTA_MERGE = "dados"
    DATA_ALVO = "20260601"
    SIMULACOES = {
        "Com Nudging": "dados/dd19735e1a81a17da86a9589ac5d1bfa.nc",
        "Sem Nudging": "dados/6b1b424d99bfc6fab01a0390722e15c1.nc",
    }

    def _mostrar_progresso(atual, total, rotulo):
        print(f"  [{atual}/{total}] {rotulo}")

    print("=" * 60)
    print(f"VALIDAÇÃO COMPLETA — {DATA_ALVO}")
    print("=" * 60)

    df_resultado = validar_dia_comparativo(
        pasta_merge=PASTA_MERGE,
        data_str=DATA_ALVO,
        simulacoes=SIMULACOES,
        salvar_json=os.path.join(PASTA_MERGE, "validacao_cache.json"),
        progresso_callback=_mostrar_progresso,
    )

    print("\nResumo (médias do dia):")
    print(resumo_veredito(df_resultado).to_string(index=False))