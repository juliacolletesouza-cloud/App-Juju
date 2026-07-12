#!/usr/bin/env python3
"""Semeia o banco com os dados reais já disponíveis:
  - Oura: export CSV Trends (18 noites)
  - Apple Watch: SÓ TREINOS (workouts) do export, conforme decisão (Watch só p/ treino)
  - Ciclo: datas de contexto.md como eventos na timeline
Uso: python3 seed.py OURA_CSV [APPLE_WORKOUTS_CSV]
"""
import csv, sys, os, re
import store
from ingest_oura import from_csv_row

def seed_oura(path):
    n = 0
    for r in csv.DictReader(open(path)):
        if not r.get("date"): continue
        date, payload = from_csv_row(r)
        store.upsert_night(date, "Oura", payload); n += 1
    print(f"Oura: {n} noites semeadas")

def seed_apple_workouts(path):
    n = 0
    for r in csv.DictReader(open(path)):
        store.upsert_workout(r["start"], "AppleWatch",
                             {"type": r.get("type"), "dur_min": float(r["dur_min"]) if r.get("dur_min") else None,
                              "kcal": r.get("kcal") or None}); n += 1
    print(f"Apple Watch: {n} treinos semeados")

def seed_cycle():
    p = os.path.join(os.path.dirname(__file__), "..", "contexto.md")
    if not os.path.exists(p): return
    n = 0
    for m in re.finditer(r"\| (\d{4}-\d{2}-\d{2}) \| (\d{4}-\d{2}-\d{2}) \|", open(p).read()):
        store.add_event(m.group(1), "ciclo", {"evento": "início de menstruação", "fim": m.group(2)}); n += 1
    print(f"Ciclo: {n} datas semeadas")

if __name__ == "__main__":
    if len(sys.argv) > 1: seed_oura(sys.argv[1])
    if len(sys.argv) > 2 and os.path.exists(sys.argv[2]): seed_apple_workouts(sys.argv[2])
    seed_cycle()
    print("contagens:", store.counts())
