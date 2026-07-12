#!/usr/bin/env python3
"""Constroi a tabela diaria alinhada da janela Apple Watch 2024.

Alinhamento (defasagem temporal correta, protocolo secao 4):
  - noite que termina na manha do dia D descreve a recuperacao medida em D
    (RHR[D], HRV[D]). Exposicao (sono) precede o desfecho (RHR da manha).
  - carga de treino do dia D-1 -> recuperacao em D (janela ~12-36h).
Saida: daily_2024.csv (uma linha por dia com dado de recuperacao).
"""
import csv, os
from datetime import datetime, date, timedelta
from collections import defaultdict

OUT = "out"

def rd(f):
    return list(csv.DictReader(open(os.path.join(OUT, f))))

# --- RHR / HRV por dia ---
rhr = {r["date"]: float(r["rhr"]) for r in rd("rhr_daily.csv") if r["rhr"]}
hrv = {r["date"]: float(r["hrv_median"]) for r in rd("hrv_daily.csv") if r["hrv_median"]}

# --- sono por wake_date (fica com o registro de maior tempo na cama do dia) ---
sleep = {}
for r in rd("sleep_episodes.csv"):
    d = r["wake_date"]
    tib = float(r["time_in_bed_min"])
    # bedtime em "minutos apos 18:00" para evitar wraparound da meia-noite
    bs = datetime.fromisoformat(r["bedtime_start"])
    bmin = (bs.hour * 60 + bs.minute) - 18 * 60
    if bmin < 0: bmin += 24 * 60          # 22:00->240 ; 01:00->420
    hh, mm = map(int, r["midsleep"].split(":"))
    midmin = hh * 60 + mm                 # midsleep 2-5h, sem wraparound
    rec = {"tib": tib, "bedtime": bmin, "midsleep": midmin, "staged": r["staged"]}
    if d not in sleep or tib > sleep[d]["tib"]:
        sleep[d] = rec

# --- carga de treino diaria (duracao total de workout no dia) ---
load = defaultdict(float)
for r in rd("workouts.csv"):
    d = r["start"][:10]
    load[d] += float(r["dur_min"])

# --- energia ativa / passos ---
act = {r["date"]: (float(r["active_kcal"]) if r["active_kcal"] else 0.0)
       for r in rd("activity_daily.csv")}

def prev(dstr, k=1):
    return (date.fromisoformat(dstr) - timedelta(days=k)).isoformat()

# --- janela 2024 (era Apple Watch): 2024-03-01 .. 2024-12-31 ---
rows = []
alldays = sorted(d for d in rhr if d.startswith("2024"))
for d in alldays:
    s = sleep.get(d, {})
    row = {
        "date": d,
        "dow": date.fromisoformat(d).weekday(),      # 0=seg
        "rhr": rhr.get(d, ""),
        "hrv": hrv.get(d, ""),
        "tib": s.get("tib", ""),
        "bedtime": s.get("bedtime", ""),
        "midsleep": s.get("midsleep", ""),
        "load_prev1": load.get(prev(d, 1), 0.0),
        "load_prev2": load.get(prev(d, 2), 0.0),
        "act_prev1": act.get(prev(d, 1), ""),
    }
    rows.append(row)

cols = ["date", "dow", "rhr", "hrv", "tib", "bedtime", "midsleep",
        "load_prev1", "load_prev2", "act_prev1"]
with open(os.path.join(OUT, "daily_2024.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
    for r in rows: w.writerow(r)

n_full = sum(1 for r in rows if r["rhr"] != "" and r["tib"] != "" and r["bedtime"] != "")
print(f"linhas 2024: {len(rows)} | com RHR+sono completo: {n_full}")
print(f"span: {rows[0]['date']} .. {rows[-1]['date']}")
