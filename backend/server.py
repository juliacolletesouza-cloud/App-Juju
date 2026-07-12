#!/usr/bin/env python3
"""Servidor Health Twin (Flask).

Rotas:
  GET  /                 -> app web
  GET  /api/state        -> estado calculado pelo cérebro (o app faz polling disso)
  GET  /webhook/oura     -> verificação do webhook Oura (challenge)
  POST /webhook/oura     -> recebe push da Oura, valida HMAC, ingere, atualiza
  POST /api/event        -> registro manual ("+" da aba Perguntar)

Segredos por env: OURA_CLIENT_ID, OURA_CLIENT_SECRET, OURA_ACCESS_TOKEN.
Deploy real: hospedar com HTTPS público e registrar a subscription na Oura.
"""
import os, hmac, hashlib, json
from datetime import date
from flask import Flask, jsonify, request, send_from_directory, Response
import store, brain
from ingest_oura import from_api_sleep

WEB = os.path.join(os.path.dirname(__file__), "..", "app", "web")
app = Flask(__name__, static_folder=None)

def build_state():
    return brain.compute(store.nights("Oura"), store.workouts(), store.events(), today=date.today())

@app.get("/api/state")
def api_state():
    return Response(json.dumps(build_state(), ensure_ascii=False), mimetype="application/json")

@app.post("/api/event")
def api_event():
    b = request.get_json(force=True, silent=True) or {}
    kind = b.get("kind") or "registro"
    payload = b.get("payload") if isinstance(b.get("payload"), dict) else None
    if payload is None:
        txt = (b.get("texto") or "").strip()
        if not txt:
            return jsonify({"ok": False, "erro": "conteúdo vazio"}), 400
        payload = {"texto": txt}
    store.add_event(b.get("date") or date.today().isoformat(), kind, payload)
    return jsonify({"ok": True})

# ---- Webhook Oura ----
@app.get("/webhook/oura")
def oura_verify():
    # Oura faz um GET de verificação e espera o challenge de volta
    ch = request.args.get("challenge")
    return jsonify({"challenge": ch}) if ch else ("", 400)

@app.post("/webhook/oura")
def oura_push():
    secret = os.environ.get("OURA_CLIENT_SECRET", "").encode()
    sig = request.headers.get("x-oura-signature", "")
    body = request.get_data()
    if secret:
        expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            return jsonify({"ok": False, "erro": "assinatura inválida"}), 401
    evt = request.get_json(force=True, silent=True) or {}
    # Em produção: buscar o objeto completo via API usando evt['data_id'] e evt['data_type'].
    # Aqui aceitamos o objeto embutido (para testes) se vier.
    obj = evt.get("object")
    if evt.get("data_type") in ("sleep", "daily_sleep") and obj:
        day, payload = from_api_sleep(obj)
        if day:
            store.upsert_night(day, "Oura", payload)
    return jsonify({"ok": True})

@app.get("/")
def index():
    return send_from_directory(WEB, "index.html")

@app.get("/<path:p>")
def assets(p):
    return send_from_directory(WEB, p)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8100)), debug=False)
