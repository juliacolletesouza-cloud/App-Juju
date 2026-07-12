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
| 2025-12-21 | 2025-12-26 | informado ⚠️ |
| 2026-01-04 | 2026-01-08 | informado |
| 2026-02-19 | 2026-02-22 | informado |
| 2026-06-15 | 2026-06-19 | informado (última) |

**⚠️ Sinalização de qualidade (NÃO é interpretação clínica):** para a covariável
H6 (ciclo → HRV) funcionar, os limites do ciclo precisam estar corretos. Os
intervalos entre INÍCIOS destas datas são atípicos para ciclos:
- 10/dez → 21/dez = **11 dias**
- 21/dez → 04/jan = **14 dias**
- 04/jan → 19/fev = **46 dias**
- 19/fev → 15/jun = **116 dias**

As duas de dezembro (10-14 e 21-26) estão a ~11 dias uma da outra — curto demais
para serem dois ciclos. Provável erro de digitação (uma delas talvez seja de
outro mês). **Precisa confirmar** antes de usar como covariável. Registrado como
veio; sinalizado como suspeito.

**Cobertura vs. dados fisiológicos:** nenhuma destas datas cai na janela do Apple
Watch 2024 → H6 continua **não testável no teste retrospectivo**. A de 15-19/jun
fica logo antes dos dados Oura (que começam 24/jun) → só relevante no go-forward.

## 5. Anomalias / eventos (doença, viagem, prova, treino, medicação)
**NÃO FORNECIDO.** → Consequência: os confundidores obrigatórios do §4 (doença,
viagem) permanecem **não aplicados**. As nulas da allowlist continuam
classificadas como coleta (tipo b/c), não ausência real.

## 6. Observações livres
**NÃO FORNECIDO.**
