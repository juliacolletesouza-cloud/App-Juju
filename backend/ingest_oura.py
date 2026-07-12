#!/usr/bin/env python3
"""Normalização Oura -> formato interno da noite.

Duas entradas, mesmo formato de saída:
  - linha do export CSV "Trends" (seed histórico)
  - objeto da API v2 /usercollection (webhook/poll, go-forward)
"""
from datetime import datetime

def _mins_from_18(dt):
    m = (dt.hour * 60 + dt.minute) - 18 * 60
    return m + 1440 if m < 0 else m

def from_csv_row(r):
    def num(k):
        try: return float(r[k])
        except (KeyError, TypeError, ValueError): return None
    bs = be = mid = None; bmin = None
    try:
        bs = datetime.fromisoformat(r["Bedtime Start"]); be = datetime.fromisoformat(r["Bedtime End"])
        mid = bs + (be - bs) / 2; bmin = _mins_from_18(bs)
    except Exception:
        pass
    tsd = num("Total Sleep Duration")
    return r["date"], {
        "hrv": num("Average HRV"), "rhr": num("Average Resting Heart Rate"),
        "rhr_low": num("Lowest Resting Heart Rate"),
        "dur_h": (tsd / 3600) if tsd else None, "eff": num("Sleep Efficiency"),
        "resp": num("Respiratory Rate"), "temp_dev": num("Temperature Deviation (°C)"),
        "bedtime_start": bs.strftime("%H:%M") if bs else None,
        "bedtime_end": be.strftime("%H:%M") if be else None,
        "bedtime_min": bmin, "midsleep": mid.strftime("%H:%M") if mid else None,
    }

def from_api_sleep(obj):
    """Objeto da API v2 (daily_sleep + sleep). Campos conforme cloud.ouraring.com/v2/docs.
    OBS: preciso validar os nomes exatos contra a doc oficial quando conectarmos de verdade."""
    day = obj.get("day") or obj.get("date")
    bs = obj.get("bedtime_start"); be = obj.get("bedtime_end")
    out = {"hrv": obj.get("average_hrv"), "rhr": obj.get("average_heart_rate"),
           "rhr_low": obj.get("lowest_heart_rate"),
           "dur_h": (obj.get("total_sleep_duration") or 0) / 3600 if obj.get("total_sleep_duration") else None,
           "eff": obj.get("efficiency"), "resp": obj.get("average_breath"),
           "temp_dev": obj.get("readiness", {}).get("temperature_deviation") if isinstance(obj.get("readiness"), dict) else None}
    try:
        b = datetime.fromisoformat(bs.replace("Z", "+00:00")); e = datetime.fromisoformat(be.replace("Z", "+00:00"))
        mid = b + (e - b) / 2
        out.update({"bedtime_start": b.strftime("%H:%M"), "bedtime_end": e.strftime("%H:%M"),
                    "bedtime_min": _mins_from_18(b), "midsleep": mid.strftime("%H:%M")})
    except Exception:
        out.update({"bedtime_start": None, "bedtime_end": None, "bedtime_min": None, "midsleep": None})
    return day, out
