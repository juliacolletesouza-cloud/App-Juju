#!/usr/bin/env python3
"""Armazenamento com proveniência (SQLite). BROAD INGESTION.

Cada linha guarda a fonte (Oura/AppleWatch) e o momento de ingestão. Nada é
sobrescrito por outra fonte: guardamos as duas e a análise escolhe a primária
(Source Resolution do brief §4). Nunca calculamos média entre fontes.
"""
import sqlite3, os, json
from datetime import datetime

DB = os.environ.get("TWIN_DB", os.path.join(os.path.dirname(__file__), "twin.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS nights (
  date TEXT NOT NULL,
  source TEXT NOT NULL,
  payload TEXT NOT NULL,      -- json normalizado da noite
  ingested_at TEXT NOT NULL,
  PRIMARY KEY (date, source)
);
CREATE TABLE IF NOT EXISTS workouts (
  start TEXT NOT NULL,
  source TEXT NOT NULL,
  payload TEXT NOT NULL,
  ingested_at TEXT NOT NULL,
  PRIMARY KEY (start, source)
);
CREATE TABLE IF NOT EXISTS events (      -- registros manuais e ciclo (timeline)
  date TEXT NOT NULL,
  kind TEXT NOT NULL,
  payload TEXT NOT NULL,
  ingested_at TEXT NOT NULL
);
"""

def conn():
    c = sqlite3.connect(DB)
    c.executescript(SCHEMA)
    return c

def upsert_night(date, source, payload):
    with conn() as c:
        c.execute("INSERT OR REPLACE INTO nights VALUES (?,?,?,?)",
                  (date, source, json.dumps(payload, ensure_ascii=False), datetime.now().isoformat(timespec="seconds")))

def upsert_workout(start, source, payload):
    with conn() as c:
        c.execute("INSERT OR REPLACE INTO workouts VALUES (?,?,?,?)",
                  (start, source, json.dumps(payload, ensure_ascii=False), datetime.now().isoformat(timespec="seconds")))

def add_event(date, kind, payload):
    with conn() as c:
        c.execute("INSERT INTO events VALUES (?,?,?,?)",
                  (date, kind, json.dumps(payload, ensure_ascii=False), datetime.now().isoformat(timespec="seconds")))

def nights(source="Oura"):
    with conn() as c:
        rows = c.execute("SELECT date,payload FROM nights WHERE source=? ORDER BY date", (source,)).fetchall()
    return [{"date": d, **json.loads(p)} for d, p in rows]

def workouts():
    with conn() as c:
        rows = c.execute("SELECT start,payload FROM workouts ORDER BY start").fetchall()
    return [{"start": s, **json.loads(p)} for s, p in rows]

def events():
    with conn() as c:
        rows = c.execute("SELECT date,kind,payload FROM events ORDER BY date").fetchall()
    return [{"date": d, "kind": k, **json.loads(p)} for d, k, p in rows]

def counts():
    with conn() as c:
        return {
            "oura_nights": c.execute("SELECT COUNT(*) FROM nights WHERE source='Oura'").fetchone()[0],
            "apple_workouts": c.execute("SELECT COUNT(*) FROM workouts WHERE source='AppleWatch'").fetchone()[0],
            "events": c.execute("SELECT COUNT(*) FROM events").fetchone()[0],
        }
