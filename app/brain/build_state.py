#!/usr/bin/env python3
"""CEREBRO do Health Twin — gera twin_state.json (deterministico, auditavel).

O app WEB so RENDERIZA este JSON. Nenhuma estatistica acontece no frontend.
Regras honradas (brief secao 0/2/6):
  - SEM escalar unico: estado = bandas por sub-estado (candidata 5).
  - Banda = posicao na propria distribuicao, nunca escala absoluta.
  - n<20 => tudo PROVISORIO; insight vira "sob observacao", nunca fabricado.
  - Cada numero carrega proveniencia (fonte) e ficha de metodo.

Uso: python3 build_state.py CAMINHO_OURA_CSV [SAIDA_JSON]
"""
import csv, json, sys, os
from datetime import datetime

OURA = sys.argv[1] if len(sys.argv) > 1 else "sample"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "web", "data", "twin_state.json")

# ---------------- carga Oura ----------------
def load_oura(path):
    rows = [r for r in csv.DictReader(open(path)) if r.get("date")]
    def num(r, k):
        try: return float(r[k])
        except (KeyError, TypeError, ValueError): return None
    recs = []
    for r in rows:
        try:
            bs = datetime.fromisoformat(r["Bedtime Start"]); be = datetime.fromisoformat(r["Bedtime End"])
            mid = bs + (be - bs) / 2
            bmin = (bs.hour * 60 + bs.minute) - 18 * 60
            if bmin < 0: bmin += 1440
        except Exception:
            bs = be = mid = None; bmin = None
        recs.append({
            "date": r["date"],
            "hrv": num(r, "Average HRV"),
            "rhr": num(r, "Average Resting Heart Rate"),
            "rhr_low": num(r, "Lowest Resting Heart Rate"),
            "dur_h": (num(r, "Total Sleep Duration") or 0) / 3600 if num(r, "Total Sleep Duration") else None,
            "eff": num(r, "Sleep Efficiency"),
            "resp": num(r, "Respiratory Rate"),
            "temp_dev": num(r, "Temperature Deviation (°C)"),
            "bedtime_start": bs.strftime("%H:%M") if bs else None,
            "bedtime_end": be.strftime("%H:%M") if be else None,
            "bedtime_min": bmin,
            "midsleep": mid.strftime("%H:%M") if mid else None,
            "act_score": num(r, "Activity Score"),
        })
    return recs

BANDS = ["baixa", "moderada", "moderada-alta", "alta"]
def band(series, val, higher_better=True):
    v = [x for x in series if x is not None]
    if val is None or len(v) < 5: return None
    pct = sum(1 for x in v if x < val) / len(v)
    if not higher_better: pct = 1 - pct
    return {"banda": BANDS[min(3, int(pct * 4))], "pct": round(pct, 2)}

# ---------------- contexto (ciclo) ----------------
def load_cycle():
    p = os.path.join(os.path.dirname(__file__), "..", "..", "contexto.md")
    dates = []
    if os.path.exists(p):
        import re
        for m in re.finditer(r"\| (\d{4}-\d{2}-\d{2}) \| (\d{4}-\d{2}-\d{2}) \|", open(p).read()):
            dates.append({"inicio": m.group(1), "fim": m.group(2)})
    return dates

# ---------------- hipoteses (do Signal Test) ----------------
def load_hypotheses():
    p = os.path.join(os.path.dirname(__file__), "..", "..", "analise", "out", "resultados.json")
    out = []
    labels = {
        "H1": "Horário de dormir → recuperação",
        "H2": "Regularidade do sono → recuperação",
        "H3": "Duração do sono → recuperação",
        "H4": "Carga de treino → recuperação",
    }
    if os.path.exists(p):
        j = json.load(open(p))
        for a in j.get("associacoes", []):
            code = a["hip"].split()[0]
            out.append({"nome": labels.get(code, a["hip"]),
                        "status": "sob observação" if not a.get("REPLICACAO_VALIDA") else "sinal preliminar",
                        "detalhe": f"n={a.get('n')}, IC cruza zero" if a.get("ic_cruza_zero") else f"n={a.get('n')}"})
    # H5/H6 nao testaveis
    out.append({"nome": "Treino noturno → sono", "status": "sob observação", "detalhe": "sono estagiado insuficiente"})
    out.append({"nome": "Fase do ciclo → HRV", "status": "sob observação", "detalhe": "covariável de controle; ciclos irregulares"})
    return out

# ---------------- montagem do estado ----------------
def build(recs):
    n = len(recs)
    hrv = [r["hrv"] for r in recs]; rhr = [r["rhr"] for r in recs]
    dur = [r["dur_h"] for r in recs]; eff = [r["eff"] for r in recs]
    resp = [r["resp"] for r in recs]; bmin = [r["bedtime_min"] for r in recs]
    last = recs[-1]

    def to_hhmm_from18(m):
        m = int(m) % 1440
        h = (m + 1080) // 60 % 24
        return f"{h:02d}:{m % 60:02d}"
    bv = sorted(x for x in bmin if x is not None)
    import statistics as st
    janela = None
    if len(bv) >= 5:
        janela = {"mediana": to_hhmm_from18(st.median(bv)),
                  "inicio": to_hhmm_from18(bv[len(bv)//4]),
                  "fim": to_hhmm_from18(bv[(3*len(bv))//4])}

    substates = [
        {"nome": "Recuperação autonômica",
         "componentes": [
            {"rotulo": "HRV noturna", "valor": last["hrv"], "unidade": "ms", "fonte": "Oura",
             **(band(hrv, last["hrv"], True) or {"banda": None})},
            {"rotulo": "FC de repouso", "valor": last["rhr"], "unidade": "bpm", "fonte": "Oura",
             **(band(rhr, last["rhr"], False) or {"banda": None})},
         ]},
        {"nome": "Suficiência de sono",
         "componentes": [
            {"rotulo": "Duração", "valor": round(last["dur_h"], 2) if last["dur_h"] else None, "unidade": "h", "fonte": "Oura",
             **(band(dur, last["dur_h"], True) or {"banda": None})},
            {"rotulo": "Eficiência", "valor": last["eff"], "unidade": "%", "fonte": "Oura",
             **(band(eff, last["eff"], True) or {"banda": None})},
         ]},
        {"nome": "Contexto respiratório",
         "componentes": [
            {"rotulo": "Freq. respiratória", "valor": last["resp"], "unidade": "rpm", "fonte": "Oura",
             **(band(resp, last["resp"], False) or {"banda": None})},
         ]},
    ]

    timeline = []
    for r in recs:
        timeline.append({"date": r["date"], "hrv": r["hrv"], "rhr": r["rhr"],
                         "dur_h": round(r["dur_h"], 2) if r["dur_h"] else None,
                         "eff": r["eff"], "bedtime": r["bedtime_start"],
                         "wake": r["bedtime_end"], "temp_dev": r["temp_dev"]})
    for c in load_cycle():
        timeline.append({"date": c["inicio"], "evento": "início de menstruação",
                         "fim": c["fim"], "tipo": "ciclo"})
    timeline.sort(key=lambda x: x["date"])

    return {
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "fonte_primaria": "Oura",
        "n_noites": n,
        "provisorio": n < 20,
        "noite_ref": last["date"],
        "sem_escalar": True,
        "nota_estado": "Estado por bandas de sub-estado (sem número único). Banda = posição na sua própria distribuição.",
        "substates": substates,
        "timeline": timeline,
        "proximo_sono": {
            "janela_realista": janela,
            "janela_natural": None,
            "janela_natural_motivo": "Exige dias sem despertador (não fornecidos). Não estimável ainda.",
            "regularidade_midsleep_min": round(st.pstdev([m for m in bmin if m is not None]), 0) if len([m for m in bmin if m is not None]) > 2 else None,
        },
        "acoes_hoje": [
            {"texto": "Coletar: rodar a âncora de horário de dormir (23:00–23:30).",
             "porque": "Com n=" + str(n) + " noites, o cérebro ainda não tem base para recomendar com confiança. A ação honesta de hoje é coletar, não prescrever."}
        ],
        "hipoteses": load_hypotheses(),
        "limitacoes": [
            "n=1 não generaliza.",
            f"Base de bandas = {n} noites (Oura). " + ("PROVISÓRIO." if n < 20 else ""),
            "Janela natural de despertar não estimável (faltam dias sem despertador).",
            "Confundidores (doença, viagem) não aplicados.",
            "Sem interpretação clínica. Ciclos irregulares são assunto de médico, não deste app.",
        ],
    }

# ---------------- sample sintetico (para o repo rodar sem dados reais) ----------------
def sample():
    import random; random.seed(7)
    from datetime import date, timedelta
    recs = []
    d0 = date(2026, 1, 1)
    for i in range(16):
        d = d0 + timedelta(days=i)
        recs.append({"date": d.isoformat(), "hrv": round(random.uniform(38, 58), 0),
                     "rhr": round(random.uniform(58, 66), 1), "rhr_low": round(random.uniform(54, 60), 1),
                     "dur_h": round(random.uniform(6.5, 8.2), 2), "eff": round(random.uniform(82, 95), 0),
                     "resp": round(random.uniform(13, 16), 2), "temp_dev": round(random.uniform(-0.2, 0.3), 2),
                     "bedtime_start": "23:0%d" % (i % 6), "bedtime_end": "07:15",
                     "bedtime_min": 300 + random.randint(-40, 40), "midsleep": "03:10", "act_score": 80})
    return recs

if __name__ == "__main__":
    recs = sample() if OURA == "sample" else load_oura(OURA)
    state = build(recs)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(state, open(OUT, "w"), indent=2, ensure_ascii=False)
    print(f"twin_state escrito em {OUT} | noites={state['n_noites']} | provisorio={state['provisorio']}")
