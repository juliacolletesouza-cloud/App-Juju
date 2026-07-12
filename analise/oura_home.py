#!/usr/bin/env python3
"""Home manual a partir dos dados ATUAIS (Oura, 18 noites — go-forward).

A Home e "como estou agora": usa a noite mais recente. Bandas = posicao na
propria distribuicao (protocolo: nunca escala absoluta). n=18 => PROVISORIO.
Sintese do estado segue a candidata 5 do teste de sensibilidade: SEM escalar,
sub-estados em banda (o teste 2024 reprovou o escalar unico).
"""
import csv, os
from datetime import datetime
import numpy as np

CSV = "/root/.claude/uploads/754dc165-3434-58bd-b89a-1ad3e14a44b0/285d2b29-oura_20260624_20260719_trends.csv"
rows = [r for r in csv.DictReader(open(CSV)) if r["date"]]

def g(r, k):
    v = r.get(k, "")
    try: return float(v)
    except (TypeError, ValueError): return None

hrv = [g(r, "Average HRV") for r in rows]
rhr = [g(r, "Average Resting Heart Rate") for r in rows]
dur = [g(r, "Total Sleep Duration") for r in rows]   # segundos
eff = [g(r, "Sleep Efficiency") for r in rows]
resp = [g(r, "Respiratory Rate") for r in rows]

def midsleep_min(r):
    try:
        bs = datetime.fromisoformat(r["Bedtime Start"]);
        be = datetime.fromisoformat(r["Bedtime End"])
        mid = bs + (be - bs) / 2
        return mid.hour * 60 + mid.minute
    except Exception: return None
mids = [midsleep_min(r) for r in rows]
bed_start = []
for r in rows:
    try:
        bs = datetime.fromisoformat(r["Bedtime Start"])
        m = (bs.hour * 60 + bs.minute) - 18 * 60
        bed_start.append(m + 1440 if m < 0 else m)
    except Exception: bed_start.append(None)

def band(series, val, higher_better=True):
    v = [x for x in series if x is not None]
    if val is None or len(v) < 5: return "sem dado"
    pct = sum(1 for x in v if x < val) / len(v)
    if not higher_better: pct = 1 - pct
    return ["baixa", "moderada", "moderada-alta", "alta"][min(3, int(pct * 4))], round(pct, 2)

last = rows[-1]
print(f"Noite mais recente: {last['date']}  (base de bandas: n={len(rows)} noites, PROVISORIO)")
print(f"  HRV noturna: {g(last,'Average HRV')} ms  -> banda {band(hrv, g(last,'Average HRV'), True)}")
print(f"  FC repouso : {g(last,'Average Resting Heart Rate')} bpm -> banda {band(rhr, g(last,'Average Resting Heart Rate'), False)}")
print(f"  Sono total : {g(last,'Total Sleep Duration')/3600:.2f} h -> banda {band(dur, g(last,'Total Sleep Duration'), True)}")
print(f"  Eficiencia : {g(last,'Sleep Efficiency')}% -> banda {band(eff, g(last,'Sleep Efficiency'), True)}")
print(f"  Freq. resp.: {g(last,'Respiratory Rate')} -> banda {band(resp, g(last,'Respiratory Rate'), False)}")

# distribuicoes para a "janela realista de dormir"
bv = [x for x in bed_start if x is not None]
def to_hhmm(m):
    m = int(m) % 1440; return f"{(m+1080)//60%24:02d}:{m%60:02d}"  # +18h volta ao relogio
print("\nJanela realista de dormir (mediana +/- IQR do bedtime, n=18):")
print(f"  mediana {to_hhmm(np.median(bv))} | IQR {to_hhmm(np.percentile(bv,25))}–{to_hhmm(np.percentile(bv,75))}")
mv = [x for x in mids if x is not None]
print(f"Regularidade do midsleep (DP, n=18): {np.std(mv):.0f} min  "
      f"(midsleep mediano {int(np.median(mv))//60:02d}:{int(np.median(mv))%60:02d})")
print("\nHRV 18 noites:", [int(x) for x in hrv if x is not None])
print("RHR 18 noites:", [round(x,1) for x in rhr if x is not None])
print("\nJanela NATURAL de despertar: NAO SEI — exige dias sem despertador (contexto.md).")
