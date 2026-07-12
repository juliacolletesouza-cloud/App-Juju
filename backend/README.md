# Backend Health Twin — ingestão automática

Servidor que ingere dados **sozinho** (sem export manual), guarda com
proveniência e serve o estado que o app renderiza. O cérebro (estatística) roda
aqui; o app só desenha.

```
Oura (nuvem) ──webhook──► /webhook/oura ─┐
Apple Watch ──iOS app───► (Fase 1b)     ─┼─► SQLite ─► brain.py ─► /api/state ─► app
registros manuais ───────► /api/event   ─┘        (proveniência)   (determinístico)
```

## Rodar local (com os dados reais já semeados)

```bash
pip install -r requirements.txt
python3 seed.py CAMINHO/oura_trends.csv CAMINHO/workouts.csv   # semeia o banco
python3 server.py                                             # http://localhost:8100
```

O app faz *polling* de `/api/state` a cada 60s — então ele **se atualiza sozinho**
conforme novos dados entram.

## Ligar a Oura de verdade (go-forward, sem export)

1. Crie um app em https://cloud.ouraring.com/ (pega `client_id` e `client_secret`).
2. Exponha este servidor com **HTTPS público** (uma hospedagem — ex.: Railway,
   Render, Fly.io). Precisa ser https para a Oura aceitar o webhook.
3. Configure os segredos no ambiente:
   ```bash
   export OURA_CLIENT_ID=...  OURA_CLIENT_SECRET=...  OURA_ACCESS_TOKEN=...
   ```
4. Registre a subscription (a Oura faz um GET de verificação em `/webhook/oura`
   e passa a mandar POST ~30s após cada sync do anel). Assinatura validada por
   HMAC com o client secret.
5. Pronto: sono/HRV/FC/prontidão entram sozinhos toda manhã.

> **"Tempo real":** o mais próximo possível é isto — push ~30s **após o anel
> sincronizar** com o celular. Nenhuma das fontes transmite ao vivo (limitação
> das plataformas, não nossa). O sono aparece de manhã, depois do sync.
> Os nomes exatos dos campos da API v2 devem ser conferidos na doc oficial
> (`cloud.ouraring.com/v2/docs`) ao conectar — ver `ingest_oura.from_api_sleep`.

## Apple Watch (Fase 1b — só treino)

Não existe API de servidor da Apple: HealthKit é **on-device**. Puxar do Watch
exige um **app iOS nativo** (Swift + HealthKit + background delivery) que empurra
os treinos para `/api/event`/um endpoint de workout. Por enquanto, os treinos
históricos entram via `seed.py` a partir do export. O app iOS é um projeto à
parte (conta Apple Developer). Decisão registrada: Apple Watch **só para treino**.

## Regras de integridade que o backend garante

- **Nunca inventa:** `brain.py` marca cada capacidade como `pronto` /
  `coletando (faltam ~X noites, pronto ~DD/MM)` / `bloqueado`. Nada de número
  fabricado.
- **Proveniência sempre:** cada linha guarda a fonte; nunca se calcula média
  entre fontes (Source Resolution do brief §4).
- **LGPD:** dado de saúde. `twin.db` é git-ignored; em produção, hospedar em
  região BR/consentida, criptografar em repouso, e tratar retenção/consentimento.
