#!/usr/bin/env python3
"""CÉREBRO do Health Twin. Determinístico e auditável. NÃO inventa.

Produz o estado que o app renderiza. Regras honradas (brief §0/§2/§6):
  - Sem escalar único: bandas por sub-estado.
  - Banda = posição na própria distribuição.
  - Cada capacidade declara se JÁ dá pra analisar; se não, diz honestamente
    "coletando — faltam ~X noites, pronto por volta de DD/MM". Sem invenção.
"""
import statistics as st
from datetime import date, datetime, timedelta

BANDS = ["baixa", "moderada", "moderada-alta", "alta"]

def _band(series, val, higher_better=True):
    v = [x for x in series if x is not None]
    if val is None or len(v) < 5:
        return None
    pct = sum(1 for x in v if x < val) / len(v)
    if not higher_better:
        pct = 1 - pct
    return {"banda": BANDS[min(3, int(pct * 4))], "pct": round(pct, 2)}

# quantas noites cada capacidade precisa para ser DEFENSÁVEL (brief §4/§7)
CAPS = [
    {"key": "estado", "nome": "Estado diário por bandas",
     "need": 14, "desbloqueia": "as bandas de sub-estado da tela Hoje"},
    {"key": "baseline", "nome": "Baseline de FC de repouso",
     "need": 28, "desbloqueia": "o que é normal pra você (janela crônica de 28 dias)"},
    {"key": "recomendacoes", "nome": "Recomendações de recuperação",
     "need": 42, "desbloqueia": "conselhos do dia baseados nas suas associações (allowlist + hold-out)"},
    {"key": "ciclo", "nome": "Efeito do ciclo na recuperação",
     "need": 90, "nota": "precisa de vários ciclos; os seus são irregulares",
     "desbloqueia": "como a fase do ciclo modula sua HRV (só covariável de controle)"},
]

def _readiness(n_oura, today):
    out = []
    for cap in CAPS:
        need = cap["need"]
        if n_oura >= need:
            out.append({**cap, "status": "pronto", "have": n_oura,
                        "faltam": 0, "pct": 1.0})
        else:
            faltam = need - n_oura
            eta = today + timedelta(days=faltam)
            out.append({**cap, "status": "coletando", "have": n_oura, "faltam": faltam,
                        "pct": round(n_oura / need, 2),
                        "eta": eta.strftime("%d/%m"),
                        "mensagem": f"Coletando — faltam ~{faltam} noites. Usando o anel todos os dias, "
                                    f"fica pronto por volta de {eta.strftime('%d/%m')}."})
    # capacidade bloqueada por dado que o tempo não resolve
    out.append({"key": "janela_natural", "nome": "Janela natural de despertar",
                "status": "bloqueado", "have": n_oura,
                "desbloqueia": "seu horário natural de acordar",
                "mensagem": "Não é questão de tempo: preciso de dias SEM despertador. "
                            "Me marque quais dias você acorda sem alarme e isto destrava."})
    return out

def compute(nights, workouts=None, events=None, today=None):
    today = today or date.today()
    nights = sorted(nights, key=lambda r: r["date"])
    n = len(nights)
    if n == 0:
        return {"vazio": True, "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "capacidades": _readiness(0, today),
                "mensagem": "Sem dados ainda. Conecte o anel Oura para começar a coletar."}

    hrv = [r.get("hrv") for r in nights]
    rhr = [r.get("rhr") for r in nights]
    dur = [r.get("dur_h") for r in nights]
    eff = [r.get("eff") for r in nights]
    resp = [r.get("resp") for r in nights]
    bmin = [r.get("bedtime_min") for r in nights]
    last = nights[-1]

    def hhmm18(m):
        m = int(m) % 1440
        return f"{((m + 1080) // 60) % 24:02d}:{m % 60:02d}"
    bv = sorted(x for x in bmin if x is not None)
    janela = None
    if len(bv) >= 5:
        janela = {"mediana": hhmm18(st.median(bv)),
                  "inicio": hhmm18(bv[len(bv) // 4]), "fim": hhmm18(bv[(3 * len(bv)) // 4])}

    substates = [
        {"nome": "Recuperação autonômica", "componentes": [
            {"rotulo": "HRV noturna", "valor": last.get("hrv"), "unidade": "ms", "fonte": "Oura",
             **( _band(hrv, last.get("hrv"), True) or {"banda": None, "pct": None})},
            {"rotulo": "FC de repouso", "valor": last.get("rhr"), "unidade": "bpm", "fonte": "Oura",
             **( _band(rhr, last.get("rhr"), False) or {"banda": None, "pct": None})},
        ]},
        {"nome": "Suficiência de sono", "componentes": [
            {"rotulo": "Duração", "valor": round(last["dur_h"], 2) if last.get("dur_h") else None, "unidade": "h", "fonte": "Oura",
             **( _band(dur, last.get("dur_h"), True) or {"banda": None, "pct": None})},
            {"rotulo": "Eficiência", "valor": last.get("eff"), "unidade": "%", "fonte": "Oura",
             **( _band(eff, last.get("eff"), True) or {"banda": None, "pct": None})},
        ]},
        {"nome": "Contexto respiratório", "componentes": [
            {"rotulo": "Freq. respiratória", "valor": last.get("resp"), "unidade": "rpm", "fonte": "Oura",
             **( _band(resp, last.get("resp"), False) or {"banda": None, "pct": None})},
        ]},
    ]

    # séries para sparkline (dados reais, visualização honesta)
    trend = {"dates": [r["date"] for r in nights],
             "rhr": rhr, "hrv": hrv, "dur": dur}

    # timeline focada na janela de rastreio ativa (Oura). Histórico antigo de
    # treino continua armazenado com proveniência, mas não inunda a tela.
    janela_inicio = nights[0]["date"]
    timeline = []
    for r in nights:
        timeline.append({"date": r["date"], "tipo": "noite", "fonte": "Oura",
                         "hrv": r.get("hrv"), "rhr": r.get("rhr"),
                         "dur_h": round(r["dur_h"], 2) if r.get("dur_h") else None,
                         "eff": r.get("eff"), "bedtime": r.get("bedtime_start"),
                         "wake": r.get("bedtime_end"), "temp_dev": r.get("temp_dev")})
    n_workouts = len(workouts or [])
    for w in (workouts or []):
        if w["start"][:10] >= janela_inicio:   # só treinos da janela ativa
            timeline.append({"date": w["start"][:10], "tipo": "treino", "fonte": "AppleWatch",
                             "wtype": w.get("type"), "dur_min": w.get("dur_min"), "kcal": w.get("kcal")})
    for e in (events or []):
        timeline.append({"date": e["date"], "tipo": e.get("kind", "evento"), **e})
    timeline.sort(key=lambda x: x["date"])
    caps = _readiness(n, today)

    return {
        "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "fonte_primaria": "Oura",
        "fontes": {"Oura (recuperação/sono)": n, "Apple Watch (treino)": n_workouts},
        "n_noites": n, "provisorio": n < 20, "noite_ref": last["date"],
        "sem_escalar": True,
        "nota_estado": "Estado por bandas de sub-estado — sem número único. Banda = posição na sua própria distribuição.",
        "substates": substates,
        "trend": trend,
        "proximo_sono": {
            "janela_realista": janela,
            "regularidade_midsleep_min": round(st.pstdev([m for m in bmin if m is not None]), 0) if len([m for m in bmin if m is not None]) > 2 else None,
        },
        "capacidades": caps,
        "timeline": timeline,
        "limitacoes": [
            "n=1 não generaliza.",
            f"Base de bandas = {n} noites (Oura)." + (" PROVISÓRIO." if n < 20 else ""),
            "Sem interpretação clínica. Ciclos irregulares são assunto de médico.",
        ],
    }
