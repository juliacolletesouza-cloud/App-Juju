# Pasta de dados — Signal Test (Fase 0)

Esta pasta está **vazia de propósito**. O Signal Test não pode começar sem os
dados reais. Não vou inventar nada para preencher — se um arquivo faltar, ele
será reportado como **faltando** no relatório de cobertura.

Coloque os 3 blocos abaixo aqui dentro. Depois me avise "dados prontos".

---

## 1. Oura — histórico completo

- **O que exportar:** conta Oura → export de **histórico completo** (não só as
  últimas 4 semanas).
- **Atenção:** o export **"Trends" é diário agregado** — serve para sono, HRV
  noturna, FC de repouso e temperatura no nível de noite, mas **não tem
  intradiário**. Se houver export mais granular disponível, traga também.
- **Onde colocar:** `dados/oura/` (CSV e/ou JSON, como vier).
- **Período mínimo desejável:** ≥ 8–9 semanas contínuas para o hold-out
  temporal 2/3 → 1/3 fazer sentido; quanto mais longo, melhor o baseline
  crônico (janela 28–60d).

## 2. Apple Health — `exportacao.xml`

- **O que exportar:** app Saúde (iPhone) → foto de perfil → **"Exportar
  Todos os Dados de Saúde"** → gera `exportar.zip`.
- Descompacte e traga o **`exportacao.xml`** (ou `export.xml`, dependendo do
  idioma do iPhone).
- **Por que é essencial:** é a **única fonte de FC intradiária** e dos workouts
  / FC de exercício / passos / energia ativa (Source Resolution do §4).
- **Onde colocar:** `dados/apple_health/exportacao.xml`.
- Observação: esse XML costuma ser **grande** (centenas de MB). Se não couber,
  me avise que definimos uma estratégia de amostragem/streaming.

## 3. `contexto.md`

- Template em `../contexto.md` (raiz do projeto). Preencha os campos marcados
  com `<preencher>` e apague os que não se aplicarem.
- Sem o contexto, os confundidores obrigatórios do §4 (dia da semana já é
  derivável, mas **fase do ciclo, doença, viagem, dias sem despertador,
  mudanças de treino/medicação**) **não existem** e várias análises da
  allowlist ficam sem controle.

---

## O que acontece depois que os dados chegarem

Sigo o §9 na ordem obrigatória:
1. **Relatório de cobertura primeiro** — quantas noites, quantos dias com HRV/FC
   repouso, buracos, artefatos, se o dataset aguenta o protocolo. **Paro aqui e
   espero seu OK.**
2. Só com o seu OK: baseline + state vector + teste de sensibilidade + resto.
