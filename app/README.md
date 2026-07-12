# Health Twin — app (v0)

App web honesto que **renderiza** o que o cérebro estatístico calcula. Nenhuma
estatística acontece no frontend: bandas, números e status vêm prontos do Python.

> **Estado:** v0 construído sobre 18 noites Oura (PROVISÓRIO). Melhora sozinho
> conforme mais dados entram — é só re-rodar o cérebro.

## Como as regras do brief viram código

| Regra (brief §0/§2/§6) | Como o app cumpre |
|---|---|
| Sem número/bateria único | Estado = **bandas por sub-estado** (candidata 5 do Signal Test) |
| LLM não faz estatística | Todo cálculo no cérebro Python; front só desenha o JSON |
| Não inventar precisão | n<20 ⇒ selo **PROVISÓRIO**; nada de insight fabricado |
| Correlação ≠ causa | Hipóteses aparecem como **"sob observação"**, nunca como fato |
| "Não sei" honesto | Janela natural de despertar = **"não sei"** (faltam dados) |
| Broad ingestion, narrow interpretation | Timeline mostra tudo; interpretação só na allowlist |
| Sem interpretação clínica | O "Perguntar" recusa conselho médico e aponta pro médico |

## Rodar

```bash
# 1. gerar o estado (cérebro) a partir do seu export Oura
python3 app/brain/build_state.py CAMINHO/oura_trends.csv
#    (sem argumento gera um sample sintético)

# 2. servir o app
cd app/web && python3 -m http.server 8099
#    abrir http://localhost:8099
```

O front busca `data/twin_state.json` (seu, local, git-ignored) e cai para
`data/twin_state.sample.json` (sintético, versionado) se o real não existir.

## Arquitetura (por que assim)

```
export Oura ──► app/brain/build_state.py ──► twin_state.json ──► app/web (3 abas)
   (dados)         (CÉREBRO determinístico)      (contrato)        (só renderiza)
```

- **Cérebro** é auditável e reproduzível (mesma lógica do Signal Test).
- **Contrato JSON** desacopla: dá pra trocar o front sem tocar na estatística.
- **Melhorar com os dados**: cada novo export → re-roda o cérebro → app atualiza.
  Quando n≥20 e a Oura tiver HRV noturna real + ciclo, as hipóteses "sob
  observação" podem virar sinal — aí o cérebro muda o status, não o front.

## Próximos passos (Fase 1, quando você quiser)
- Ingestão automática via **Oura API v2** (substitui o export manual).
- Persistência real dos registros do "+" na timeline.
- Re-rodar a allowlist a cada semana e promover hipóteses que replicarem.
