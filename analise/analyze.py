#!/usr/bin/env python3
"""Motor estatistico do Signal Test — janela Apple Watch 2024.

Determinista (seed fixa). Metodos pre-registrados (protocolo secao 4):
  baseline robusto (mediana movel + MAD); bandas por quantis proprios;
  Theil-Sen + IC por block bootstrap; teste por permutacao circular em blocos
  (respeita autocorrelacao); FDR Benjamini-Hochberg; hold-out temporal 2/3->1/3.
Saida: out/resultados.json + texto no stdout.
"""
import csv, json, os
import numpy as np
from scipy.stats import theilslopes

RNG = np.random.default_rng(42)
OUT = "out"

# ---------- carga ----------
rows = list(csv.DictReader(open(os.path.join(OUT, "daily_2024.csv"))))
def col(name, filt=None):
    out = []
    for r in rows:
        v = r[name]
        out.append(float(v) if v not in ("", None) else np.nan)
    a = np.array(out, float)
    if filt: a = filt(a)
    return a

dates = [r["date"] for r in rows]
rhr = col("rhr")
hrv = col("hrv")
tib = col("tib"); tib = np.where((tib < 180) | (tib > 720), np.nan, tib)  # winsor fisiologico
bedtime = col("bedtime")
midsleep = col("midsleep")
load1 = col("load_prev1")
dow = col("dow")
N = len(rows)

# ---------- baseline robusto ----------
def roll_median(x, w):
    out = np.full_like(x, np.nan, float)
    for i in range(len(x)):
        lo = max(0, i - w + 1)
        seg = x[lo:i + 1]; seg = seg[~np.isnan(seg)]
        if len(seg) >= max(5, w // 4): out[i] = np.median(seg)
    return out

def roll_mad(x, w):
    out = np.full_like(x, np.nan, float)
    for i in range(len(x)):
        lo = max(0, i - w + 1)
        seg = x[lo:i + 1]; seg = seg[~np.isnan(seg)]
        if len(seg) >= max(5, w // 4):
            out[i] = np.median(np.abs(seg - np.median(seg))) * 1.4826
    return out

CHRONIC = 42
rhr_base = roll_median(rhr, CHRONIC); rhr_mad = roll_mad(rhr, CHRONIC)
hrv_base = roll_median(hrv, CHRONIC); hrv_mad = roll_mad(hrv, CHRONIC)
tib_base = roll_median(tib, CHRONIC); tib_mad = roll_mad(tib, CHRONIC)

def stable_baseline(base, mad):
    """MAD tipico vs. amplitude do baseline: baseline distinguivel de ruido?"""
    b = base[~np.isnan(base)]; m = mad[~np.isnan(mad)]
    if len(b) < 20: return None
    return {"amplitude_baseline": round(float(np.percentile(b, 90) - np.percentile(b, 10)), 2),
            "mad_tipico": round(float(np.median(m)), 2),
            "razao_sinal_ruido": round(float((np.percentile(b, 90) - np.percentile(b, 10)) / np.median(m)), 2)}

baseline_diag = {"rhr": stable_baseline(rhr_base, rhr_mad),
                 "hrv": stable_baseline(hrv_base, hrv_mad)}

# ---------- state vector (4 sub-estados) ----------
def pct_rank(x):
    """posicao de cada ponto na propria distribuicao (0..1), robusto a NaN."""
    out = np.full_like(x, np.nan, float)
    valid = ~np.isnan(x); v = x[valid]
    if len(v) < 5: return out
    order = v.argsort().argsort()
    out[valid] = order / (len(v) - 1)
    return out

# 1. Recuperacao autonomica: RHR baixa=bom, HRV alta=bom (desvio vs baseline/MAD)
rhr_z = (rhr_base - rhr) / rhr_mad          # positivo = melhor que baseline
hrv_z = (hrv - hrv_base) / hrv_mad
autonomic = np.nanmean(np.vstack([rhr_z, hrv_z]), axis=0)
# 2. Suficiencia de sono: proximidade da necessidade (mediana pessoal de TIB)
need = np.nanmedian(tib)
sleep_suff = -np.abs(tib - need) / np.nanmedian(np.abs(tib - need))
# 3. Carga recente: razao aguda/cronica; extremos (alto OU baixo) = pior
acute = np.array([np.nansum(load1[max(0, i-6):i+1]) for i in range(N)], float)
chronic_l = np.array([np.nanmedian(load1[max(0, i-27):i+1]) if i >= 6 else np.nan for i in range(N)], float)
ratio = np.where(chronic_l > 0, acute / (chronic_l * 7 + 1e-9), np.nan)
recent_load = -np.abs(np.log(ratio + 1e-6))
# 4. Contexto circadiano: desvio do midsleep pessoal (modulador, nao bom/ruim)
circ = -np.abs(midsleep - np.nanmedian(midsleep)) / (np.nanmedian(np.abs(midsleep - np.nanmedian(midsleep))) + 1e-9)

subs = {"autonomic": autonomic, "sleep_suff": sleep_suff,
        "recent_load": recent_load, "circadian": circ}
subs_pct = {k: pct_rank(v) for k, v in subs.items()}

# ---------- TESTE DE SENSIBILIDADE (secao 6) ----------
core = ["autonomic", "sleep_suff", "recent_load"]  # circadiano e modulador
M = np.vstack([subs_pct[k] for k in core])          # 3 x N
valid_days = ~np.any(np.isnan(M), axis=0)
Mv = M[:, valid_days]

def to_bands(score, q=(0.25, 0.5, 0.75)):
    s = score.copy(); out = np.full_like(s, np.nan)
    v = s[~np.isnan(s)]
    if len(v) < 8: return out
    cuts = np.quantile(v, q)
    out[~np.isnan(s)] = np.digitize(v, cuts)   # 0=baixa,1=mod,2=mod-alta,3=alta
    return out

specs = {}
specs["min_limit"] = np.min(Mv, axis=0)
specs["equal_weight"] = np.mean(Mv, axis=0)
# PCA-1
Mc = Mv - Mv.mean(axis=1, keepdims=True)
U, S, Vt = np.linalg.svd(Mc, full_matrices=False)
pc1 = Vt[0] * S[0]
if np.corrcoef(pc1, np.mean(Mv, axis=0))[0, 1] < 0: pc1 = -pc1
specs["pca1"] = (pc1 - pc1.min()) / (np.ptp(pc1) + 1e-9)
specs["mean_two_worst"] = np.mean(np.sort(Mv, axis=0)[:2], axis=0)
# candidata 5 "sem escalar": banda = banda do pior sub-estado (regra sobre o vetor)
sub_bands = np.vstack([to_bands(Mv[i]) for i in range(3)])
specs["rules_worst"] = np.min(sub_bands, axis=0)   # ja em banda

bands = {}
for name, sc in specs.items():
    bands[name] = sc if name == "rules_worst" else to_bands(sc)

# taxa de troca de banda entre pares de especificacoes
names = list(bands.keys())
switch = {}
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a, b = bands[names[i]], bands[names[j]]
        m = ~np.isnan(a) & ~np.isnan(b)
        switch[f"{names[i]} vs {names[j]}"] = round(float(np.mean(a[m] != b[m])), 3)
mean_switch = round(float(np.mean(list(switch.values()))), 3)

# ---------- ASSOCIACOES (allowlist testavel) ----------
def resid(x):
    """desvio do baseline cronico -> associacao within-person, remove drift lento."""
    b = roll_median(x, CHRONIC)
    return x - b

def block_perm_p(x, y, obs, nperm=2000, L=7):
    """permutacao por deslocamento circular do desfecho (respeita autocorrelacao)."""
    m = ~np.isnan(x) & ~np.isnan(y)
    xx, yy = x[m], y[m]; n = len(xx)
    if n < 20: return np.nan
    cnt = 0
    for _ in range(nperm):
        shift = RNG.integers(L, n - L)
        yp = np.roll(yy, shift)
        s = theilslopes(yp, xx)[0]
        if abs(s) >= abs(obs) - 1e-12: cnt += 1
    return (cnt + 1) / (nperm + 1)

def block_boot_ci(x, y, nboot=1000, L=7):
    m = ~np.isnan(x) & ~np.isnan(y)
    xx, yy = x[m], y[m]; n = len(xx)
    if n < 20: return (np.nan, np.nan)
    nb = int(np.ceil(n / L)); slopes = []
    for _ in range(nboot):
        starts = RNG.integers(0, n, nb)
        idx = np.concatenate([np.arange(s, s + L) % n for s in starts])[:n]
        try: slopes.append(theilslopes(yy[idx], xx[idx])[0])
        except Exception: pass
    return (float(np.percentile(slopes, 2.5)), float(np.percentile(slopes, 97.5)))

def assoc(xr, yr, name, direction):
    m = ~np.isnan(xr) & ~np.isnan(yr)
    n = int(m.sum())
    if n < 20:
        return {"hip": name, "n": n, "status": "n_insuficiente"}
    slope = float(theilslopes(yr[m], xr[m])[0])
    lo, hi = block_boot_ci(xr, yr)
    p = block_perm_p(xr, yr, slope)
    # hold-out temporal 2/3 -> 1/3
    idx = np.where(m)[0]; cut = idx[int(len(idx) * 2 / 3)]
    tr = m & (np.arange(N) < cut); te = m & (np.arange(N) >= cut)
    s_tr = float(theilslopes(yr[tr], xr[tr])[0]) if tr.sum() >= 15 else np.nan
    s_te = float(theilslopes(yr[te], xr[te])[0]) if te.sum() >= 15 else np.nan
    replicou = (not np.isnan(s_tr) and not np.isnan(s_te)
                and np.sign(s_tr) == np.sign(s_te) and abs(s_te) > 0.2 * abs(s_tr))
    ic_cruza_zero = (lo <= 0 <= hi)
    # replicacao SO conta se: sinal replica no hold-out E o efeito e significativo
    # (p<0.10) E o IC nao cruza zero. Sinal replicando num efeito nulo = confundidor/ruido.
    replicacao_valida = bool(replicou and (p < 0.10) and (not ic_cruza_zero))
    return {"hip": name, "n": n, "direcao_esperada": direction,
            "theil_sen_slope": round(slope, 4), "ic95": [round(lo, 4), round(hi, 4)],
            "ic_cruza_zero": bool(ic_cruza_zero),
            "p_perm": round(p, 4), "slope_treino": round(s_tr, 4) if not np.isnan(s_tr) else None,
            "slope_holdout": round(s_te, 4) if not np.isnan(s_te) else None,
            "sinal_replica_holdout": bool(replicou),
            "REPLICACAO_VALIDA": replicacao_valida}

# outcome: RHR (desvio do baseline). Menor RHR = melhor recuperacao.
rhr_r = resid(rhr)
# regularidade: SD movel 7d do midsleep
reg = np.array([np.nanstd(midsleep[max(0, i-6):i+1]) if np.sum(~np.isnan(midsleep[max(0,i-6):i+1]))>=4 else np.nan for i in range(N)])

results = []
results.append(assoc(resid(bedtime), rhr_r, "H1 horario_dormir -> RHR", "dormir tarde -> RHR maior (pior)"))
results.append(assoc(resid(reg),     rhr_r, "H2 irregularidade_sono -> RHR", "mais irregular -> RHR maior"))
results.append(assoc(resid(tib),     rhr_r, "H3 duracao_sono(TIB) -> RHR", "mais sono -> RHR menor (melhor)"))
results.append(assoc(resid(load1),   rhr_r, "H4 carga_treino_D-1 -> RHR", "carga maior -> RHR maior 24h"))

tested = [r for r in results if r.get("p_perm") is not None and "p_perm" in r]
# FDR Benjamini-Hochberg
ps = [r["p_perm"] for r in tested]
order = np.argsort(ps); m_t = len(ps)
fdr = {}
for rank, oi in enumerate(order, 1):
    fdr[id(tested[oi])] = min(1.0, ps[oi] * m_t / rank)
for r in tested:
    r["q_fdr"] = round(float(fdr[id(r)]), 4)

not_tested = {
    "H5 treino_noturno -> latencia/eficiencia sono":
        "NAO TESTAVEL nesta janela: eficiencia/latencia exigem sono estagiado; so 14-15 noites estagiadas em 2024 (tipo b/c: coleta).",
    "H6 fase_ciclo -> HRV":
        "NAO TESTAVEL nesta janela: sem datas de menstruacao em 2024 (Apple so tem 9 registros, todos 2026). Aguarda contexto.md (tipo b: coleta).",
}

summary = {
    "janela": f"{dates[0]} .. {dates[-1]}",
    "n_dias": N,
    "baseline_diag": baseline_diag,
    "estado_necessidade_sono_min": round(float(need), 1),
    "sensibilidade": {"taxa_troca_media": mean_switch, "pares": switch,
                      "criterio_protocolo": "estavel se < 0.15-0.20"},
    "associacoes": results,
    "nao_testaveis": not_tested,
}
json.dump(summary, open(os.path.join(OUT, "resultados.json"), "w"), indent=2, ensure_ascii=False)

# ---------- impressao legivel ----------
print("=" * 70)
print(f"SIGNAL TEST — janela Apple Watch {summary['janela']} (n={N} dias)")
print("=" * 70)
print("\n[BASELINE — sinal vs ruido]")
for k, v in baseline_diag.items():
    if v: print(f"  {k.upper()}: amplitude p10-p90={v['amplitude_baseline']} | "
                f"MAD tipico={v['mad_tipico']} | razao S/R={v['razao_sinal_ruido']}")
print("\n[TESTE DE SENSIBILIDADE DO ESTADO]")
print(f"  taxa de troca de banda MEDIA entre especificacoes: {mean_switch}  "
      f"(criterio: estavel se < 0.15-0.20)")
for k, v in sorted(switch.items(), key=lambda x: x[1]):
    print(f"    {k:38s} {v}")
print("\n[ASSOCIACOES — allowlist testavel]")
for r in results:
    if r.get("status") == "n_insuficiente":
        print(f"  {r['hip']}: n={r['n']} INSUFICIENTE"); continue
    print(f"  {r['hip']}  (n={r['n']})")
    print(f"    slope={r['theil_sen_slope']}  IC95={r['ic95']} (cruza_zero={r['ic_cruza_zero']})  "
          f"p_perm={r['p_perm']}  q_FDR={r.get('q_fdr')}")
    print(f"    treino={r['slope_treino']}  holdout={r['slope_holdout']}  "
          f"sinal_replica={r['sinal_replica_holdout']}  >>> REPLICACAO_VALIDA={r['REPLICACAO_VALIDA']}")
print("\n[NAO TESTAVEIS nesta janela]")
for k, v in not_tested.items(): print(f"  {k}\n    -> {v}")
