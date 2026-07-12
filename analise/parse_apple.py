#!/usr/bin/env python3
"""Streaming parser do Apple Health export.

Le o XML via stdin (unzip -p ... | python parse_apple.py OUTDIR) e emite CSVs
diarios limpos. Nao carrega o XML inteiro na memoria (iterparse + clear).

Regras de proveniencia (Source Resolution, protocolo secao 4, com o desvio
ACORDADO: nesta janela o Apple Watch e primario porque a Oura tem so 18 noites):
  - RestingHeartRate  -> Apple Watch (1/dia). Desfecho de recuperacao primario.
  - HRV SDNN          -> amostras pontuais (spot). Secundario, com ressalva.
  - SleepAnalysis     -> episodios agrupados; estagiado se houver, senao InBed.
  - Workout           -> carga de treino (duracao, energia).
Datas: mantem hora local (wall clock) ignorando o offset de tz (consistente -0300).
"""
import sys, csv, os
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

def parse_dt(s):
    # formato "2024-06-24 07:00:00 -0300" -> naive local
    return datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")

rhr = {}            # date -> list de bpm
hrv_all = []        # (datetime, ms)
sleep_recs = []     # (start_dt, end_dt, value, source)
workouts = []       # (start_dt, end_dt, dur_min, kcal, wtype)
act_energy = {}     # date -> kcal
steps = {}          # date -> passos
resp = {}           # date -> list freq resp

src = sys.stdin.buffer
ctx = ET.iterparse(src, events=("end",))
n = 0
for _, el in ctx:
    tag = el.tag
    if tag == "Record":
        t = el.get("type", "")
        try:
            if t == "HKQuantityTypeIdentifierRestingHeartRate":
                d = el.get("startDate")[:10]
                rhr.setdefault(d, []).append(float(el.get("value")))
            elif t == "HKQuantityTypeIdentifierHeartRateVariabilitySDNN":
                hrv_all.append((parse_dt(el.get("startDate")), float(el.get("value"))))
            elif t == "HKCategoryTypeIdentifierSleepAnalysis":
                v = el.get("value", "").replace("HKCategoryValueSleepAnalysis", "")
                sleep_recs.append((parse_dt(el.get("startDate")), parse_dt(el.get("endDate")),
                                   v, el.get("sourceName", "")))
            elif t == "HKQuantityTypeIdentifierActiveEnergyBurned":
                d = el.get("startDate")[:10]
                act_energy[d] = act_energy.get(d, 0.0) + float(el.get("value"))
            elif t == "HKQuantityTypeIdentifierStepCount":
                d = el.get("startDate")[:10]
                steps[d] = steps.get(d, 0.0) + float(el.get("value"))
            elif t == "HKQuantityTypeIdentifierRespiratoryRate":
                d = el.get("startDate")[:10]
                resp.setdefault(d, []).append(float(el.get("value")))
        except (TypeError, ValueError):
            pass
    elif tag == "Workout":
        try:
            st = parse_dt(el.get("startDate")); en = parse_dt(el.get("endDate"))
            dur = el.get("duration")
            dur_min = float(dur) if dur else (en - st).total_seconds() / 60.0
            kcal = ""
            # energia pode estar em atributo ou em WorkoutStatistics filho
            for ws in el.findall("WorkoutStatistics"):
                if ws.get("type") == "HKQuantityTypeIdentifierActiveEnergyBurned":
                    kcal = ws.get("sum", "")
            wtype = el.get("workoutActivityType", "").replace("HKWorkoutActivityType", "")
            workouts.append((st, en, round(dur_min, 1), kcal, wtype))
        except (TypeError, ValueError):
            pass
    n += 1
    el.clear()

# ---- agrupa sono em episodios (gap < 60 min = mesma noite) ----
sleep_recs.sort(key=lambda r: r[0])
episodes = []
cur = None
for st, en, v, source in sleep_recs:
    if v == "InBed" and source and "iphone" in source.lower():
        kind = "inbed"
    elif v.startswith("Asleep"):
        kind = "asleep"
    elif v == "Awake":
        kind = "awake"
    elif v == "InBed":
        kind = "inbed"
    else:
        kind = "other"
    if cur is None or st - cur["end"] > timedelta(minutes=60):
        if cur: episodes.append(cur)
        cur = {"start": st, "end": en, "asleep": timedelta(), "inbed": timedelta(),
               "staged": False, "sources": set()}
    cur["end"] = max(cur["end"], en)
    dur = en - st
    if kind == "asleep":
        cur["asleep"] += dur
        if v in ("AsleepCore", "AsleepDeep", "AsleepREM"):
            cur["staged"] = True
    if kind in ("inbed", "asleep", "awake"):
        cur["inbed"] += dur
    cur["sources"].add(source)
if cur: episodes.append(cur)

# noite atribuida a data do despertar; filtra sonecas (< 3h in-bed)
with open(os.path.join(OUT, "sleep_episodes.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["wake_date", "bedtime_start", "bedtime_end", "time_in_bed_min",
                "asleep_min", "midsleep", "staged", "source"])
    for e in episodes:
        tib = e["inbed"].total_seconds() / 60.0
        if tib < 180:  # ignora soneca/registro curto
            continue
        mid = e["start"] + (e["end"] - e["start"]) / 2
        asleep = e["asleep"].total_seconds() / 60.0
        w.writerow([e["end"].date(), e["start"].isoformat(sep=" "),
                    e["end"].isoformat(sep=" "), round(tib, 1),
                    round(asleep, 1) if asleep > 0 else "",
                    mid.strftime("%H:%M"), int(e["staged"]),
                    ";".join(sorted(s for s in e["sources"] if s))])

def median(xs):
    xs = sorted(xs); k = len(xs)
    return (xs[k//2] if k % 2 else (xs[k//2-1]+xs[k//2])/2) if k else ""

with open(os.path.join(OUT, "rhr_daily.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["date", "rhr"])
    for d in sorted(rhr): w.writerow([d, round(median(rhr[d]), 1)])

# HRV: mediana diaria + mediana janela noturna (00:00-08:00)
hrv_day = {}; hrv_night = {}
for dt, ms in hrv_all:
    d = dt.date().isoformat()
    hrv_day.setdefault(d, []).append(ms)
    if dt.hour < 8:
        hrv_night.setdefault(d, []).append(ms)
with open(os.path.join(OUT, "hrv_daily.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["date", "hrv_median", "hrv_n", "hrv_night_median", "hrv_night_n"])
    for d in sorted(hrv_day):
        w.writerow([d, round(median(hrv_day[d]), 1), len(hrv_day[d]),
                    round(median(hrv_night[d]), 1) if d in hrv_night else "",
                    len(hrv_night.get(d, []))])

with open(os.path.join(OUT, "activity_daily.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["date", "active_kcal", "steps", "resp_rate"])
    days = set(act_energy) | set(steps) | set(resp)
    for d in sorted(days):
        w.writerow([d, round(act_energy.get(d, 0), 1), int(steps.get(d, 0)),
                    round(median(resp[d]), 2) if d in resp else ""])

with open(os.path.join(OUT, "workouts.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["start", "end", "dur_min", "kcal", "type"])
    for st, en, dur, kcal, wtype in sorted(workouts):
        w.writerow([st.isoformat(sep=" "), en.isoformat(sep=" "), dur, kcal, wtype])

print(f"registros lidos: {n}", file=sys.stderr)
print(f"rhr dias={len(rhr)} | hrv dias={len(hrv_day)} | sono episodios={len(episodes)} "
      f"| workouts={len(workouts)} | atividade dias={len(set(act_energy)|set(steps))}",
      file=sys.stderr)
