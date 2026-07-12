# contexto.md — dados reais fornecidos por Julia

> Preenchido em 2026-07-12 com o que a Julia forneceu. Campos ainda não
> fornecidos ficam marcados como **NÃO FORNECIDO** — não são inventados.

## 1. Rotina por dia da semana
**NÃO FORNECIDO** (Julia informou que não tem esses dados no momento).

## 2. Dias sem despertador
**NÃO FORNECIDO.** → Consequência: a **"janela natural observada de despertar"**
(capacidade 3) permanece **não estimável**. Não será inventada.

## 3. Horário que preciso acordar amanhã
**NÃO FORNECIDO.**

## 4. Fase do ciclo — datas de início de menstruação (fornecidas)

| Início | Fim | Fonte |
|---|---|---|
| 2025-12-10 | 2025-12-14 | informado |
| 2025-12-21 | 2025-12-26 | informado (dois ciclos em dez — CONFIRMADO por Julia) |
| 2026-01-04 | 2026-01-08 | informado |
| 2026-02-19 | 2026-02-22 | informado |
| 2026-06-15 | 2026-06-19 | informado (última) |

**Característica do dado (NÃO é interpretação clínica — isso é assunto de médico,
não deste teste):** os intervalos entre INÍCIOS são muito variáveis —
11 → 14 → 46 → 116 dias. Ou seja, **ciclos irregulares**. Implicação de MÉTODO
para H6: a "fase do ciclo" tem que ser derivada das **datas reais** informadas,
**nunca** de um modelo fixo de 28 dias (que mentiria aqui). Datas confirmadas
pela Julia; usar como limites empíricos.

**Cobertura vs. dados fisiológicos:** nenhuma destas datas cai na janela do Apple
Watch 2024 → H6 continua **não testável no teste retrospectivo**. A de 15-19/jun
fica logo antes dos dados Oura (que começam 24/jun) → só relevante no go-forward.

## 5. Anomalias / eventos (doença, viagem, prova, treino, medicação)
**NÃO FORNECIDO.** → Consequência: os confundidores obrigatórios do §4 (doença,
viagem) permanecem **não aplicados**. As nulas da allowlist continuam
classificadas como coleta (tipo b/c), não ausência real.

## 6. Observações livres
**NÃO FORNECIDO.**
