# HEALTH TWIN — BRIEF DE PROJETO + SIGNAL TEST PROTOCOL v1.1

> **TAREFA ATUAL: apenas a Fase 0 (Signal Test). NÃO construir o aplicativo ainda.**

---

## 0. CONTEXTO E REGRAS DE ENGAJAMENTO

Você é meu cofundador técnico + bioestatístico. Regras não-negociáveis:

- **Não elogie a ideia.** Critique premissas. Se algo for cientificamente ruim, diga.
- **Nunca confunda correlação com causalidade.** Nem no código, nem no texto de saída.
- **Não invente precisão.** Se não dá pra saber, o output é "não sei".
- **LLM não faz estatística.** Todo cálculo é código determinístico e auditável.
- **Não invente dados que não estão nos arquivos.** Faltou? Reporte como faltando.
- Se uma API/limitação for incerta, diga "preciso verificar a documentação oficial".
- Responda em português do Brasil.

---

## 1. O PRODUTO (definição condensada)

> **"Um app que sabe como meu corpo está agora, estima para onde ele está indo, aprende meus padrões ao longo do tempo e me diz o que realmente importa fazer hoje."**

O **Health Twin** é o cérebro longitudinal por trás de tudo. Não é uma tela nem um score.

### Princípio central de escopo
**BROAD INGESTION, NARROW INTERPRETATION.**
Muitos dados podem ser *ingeridos, estruturados, armazenados com proveniência e colocados na timeline*. Pouquíssimos podem *gerar correlação, insight, recomendação ou interpretação clínica*.

Níveis de capacidade por tipo de dado (declarar explicitamente para cada um):
`ingest → store → visualize → correlate → generate insight → generate recommendation → clinical interpretation`

Só se raciocina automaticamente sobre relações que estão na **allowlist analítica** (§5). Fora dela, o dado existe como memória e contexto — nunca como narrativa causal.

Exemplo: "Ferritina 18 ng/mL" pode aparecer na timeline. Isso **não** autoriza dizer que ela causou fadiga.

### As 6 capacidades (uma só mente, não 6 módulos)
1. **Estado fisiológico** (prontidão) — bandas, sem falsa precisão
2. **Ativação fisiológica** — retrospectiva, nunca "tempo real"
3. **Próximo sono** — janela de dormir + desaceleração + janela natural de despertar
4. **Tendências / hipóteses sob observação** — conservador, silencioso por padrão
5. **Previsão** — transversal, sempre com incerteza e rótulo
6. **Health Twin** — baseline, desvios, aprendizado, explicação

### Arquitetura de informação (3 abas, e só)
- **HOJE** — como estou / por quê / o que fazer (1–3 ações). Progressive disclosure via "Por que estou vendo isso?"
- **MINHA HISTÓRIA** — timeline longitudinal multimodal
- **PERGUNTAR** — conversa + entrada de dados externos (duas affordances distintas: `+` para registrar, campo para perguntar)

---

## 2. DECISÕES JÁ TOMADAS (não reabrir sem motivo forte)

| Tema | Decisão |
|---|---|
| "Energia: 82" | **Rejeitado.** Falsa precisão. Sem número de dois dígitos. |
| Estado fisiológico | **State vector interno de 4 sub-estados** + síntese linguística na interface. O backend NÃO assume uma variável latente única chamada "Prontidão". |
| Bateria visual | Permitida, mas o preenchimento = **posição dela na própria distribuição histórica**, nunca escala absoluta. |
| Como sintetizar o vetor na bateria | **NÃO FIXADO A PRIORI.** Decidido pelo teste de sensibilidade (§6). |
| "Horário biologicamente ideal para acordar" | **Rejeitado como formulação.** Substituído por *"sua janela natural observada"* (empírica, dias sem despertador). |
| Ativação fisiológica em tempo real | **Impossível** via HealthKit. Só retrospectiva/delayed. |
| Loop de aprendizado (recomendação → aderência → resposta) | **É o fosso competitivo.** Não é detalhe. |

### State vector (4 sub-estados)
| Sub-estado | Componentes | Direção |
|---|---|---|
| Recuperação autonômica | HRV noturna, FC repouso vs. baseline | HRV↑ e FCrep↓ = melhor |
| Suficiência de sono | duração vs. necessidade estimada, eficiência, débito | perto da necessidade = melhor |
| Carga recente | razão carga aguda/crônica | muito alta OU muito baixa = pior |
| Contexto circadiano/vigília | horas acordada, alinhamento com padrão | modulador, não "bom/ruim" |

---

## 3. FASE 0 — SIGNAL TEST (a única tarefa agora)

**Objetivo:** os meus dados reais contêm sinal suficiente para produzir a Home do Health Twin de forma defensável? Não é "o app é bom" — é "o cérebro tem o que aprender".

**Entregável final:** a Home manual preenchida com dados reais + ficha de metodologia de cada número + scorecard de 8 dimensões.

### Dados de entrada
- **Oura** — export de conta com **histórico completo** (não apenas 4 semanas). O export "Trends" é **diário agregado** e não tem dados intradiários.
- **Apple Health** — `exportacao.xml` (do `exportar.zip`). **Essencial**: é a única fonte de FC intradiária.
- **Contexto (arquivo `contexto.md` que eu vou escrever):** rotina por dia da semana, dias sem despertador, anomalias (doença/viagem/prova/mudança de treino/medicamento/suplemento), datas de início de menstruação, horário que preciso acordar amanhã.

### Ordem de execução (obrigatória)
1. **Relatório de cobertura primeiro.** Nunca rodar análise antes de me dizer se o dataset aguenta.
2. Só depois, as análises.

---

## 4. MÉTODOS ESTATÍSTICOS (pré-registrados)

- **Baseline:** mediana móvel + MAD (janela 28–60d) para o crônico; EWMA (meia-vida ~7d) para o agudo. **Estatística robusta, nunca média/DP.**
- **Bandas:** quantis da *própria* distribuição dela (alta / moderada-alta / moderada / baixa).
- **Tendência:** regressão robusta **Theil-Sen** + IC por **block bootstrap** (respeita autocorrelação — regressão OLS ingênua MENTE aqui). Changepoint por segmentação.
- **Associações:** within-person, dia-a-dia, com **defasagem temporal correta** (exposição sempre ANTES do desfecho).
- **Teste:** **permutation test em blocos** (não p-valor ingênuo — os dados são autocorrelacionados).
- **Múltiplos testes:** **FDR Benjamini-Hochberg** sobre as hipóteses da allowlist.
- **Hold-out temporal:** derivar nos primeiros 2/3, **replicar no 1/3 final**. Sem replicação = **não é achado**.
- **n mínimo:** 20 observações comparáveis. Abaixo disso → "hipótese sob observação", **jamais** insight.
- **Confundidores obrigatórios:** dia da semana, fase do ciclo, carga de treino, doença, viagem.

### Source Resolution (fixar antes de analisar)
- Sono, HRV noturna, FC repouso, temperatura → **Oura** (primária)
- Workouts, FC de exercício, FC intradiária, passos, energia ativa → **Apple Watch/HealthKit** (primária)
- **Nunca calcular média entre fontes.** Usar a primária; a secundária só checa cobertura/consistência.

---

## 5. ALLOWLIST ANALÍTICA (exatamente 6 hipóteses — nada fora disto)

Direção pré-especificada. Qualquer coisa "interessante" fora da lista vira *hipótese sob observação futura*, **nunca** achado deste teste.

1. Horário de dormir → recuperação no dia seguinte (HRV / FC repouso)
2. Regularidade do sono (variabilidade do midsleep) → recuperação
3. Duração do sono → recuperação
4. Carga de treino → recuperação em 24–48h
5. Treino noturno → latência / eficiência do sono
6. Fase do ciclo → HRV (**apenas covariável de controle**, não insight)

---

## 6. TESTE DE SENSIBILIDADE DO ESTADO (crítico — não pular)

Nenhuma especificação é escolhida a priori. Candidatas:
1. Min-limitante (bateria = pior sub-estado)
2. Equal-weight
3. PCA-1
4. Média dos dois piores
5. **Sem escalar** — bateria dirigida por regras sobre o vetor

**Critério de decisão, nesta ordem:**
1. **Estabilidade** — taxa de troca de banda entre especificações. Se nenhuma ficar **abaixo de ~15–20%**, a resposta é a candidata 5 e **o produto não terá escalar**.
2. **Preservação de informação** — a especificação distingue estados fisiologicamente opostos ou os colapsa? (equal-weight tende a falhar aqui)
3. **Explicabilidade** — dá pra escrever o "Por que estou vendo isso?" honestamente?
4. **Coerência** — nos dias marcados como anômalos (doença, treino pesado, noite ruim), a banda cai onde deveria? Uma spec que põe dia de gripe em "prontidão alta" está reprovada, por mais estável que seja.

Empate → **a mais simples de explicar**, não a mais sofisticada.

---

## 7. SCORECARD DE VIABILIDADE (8 dimensões INDEPENDENTES)

Cada uma recebe 🟢/🟡/🔴 **separadamente**. **Nenhuma mata a tese sozinha.**

| Dimensão | 🟢 | 🟡 | 🔴 |
|---|---|---|---|
| Data Coverage | ≥80% das noites | 50–80% | <50% ou artefatos |
| Baseline Learnability | robusto e estável | estável em algumas métricas | indistinguível de ruído |
| State Estimation | sub-estados estáveis na sensibilidade | vetor ok, escalar instável | bandas trocam sob qualquer respec. |
| Sleep Recommendation | janela realista + natural | só a realista | sono insuficiente |
| Trend Detection | detecta real E fica em silêncio quando não há | detecta, silêncio não testado | vê tendência onde é ruído |
| Hypothesis Replication | ≥1 replica no hold-out | sinais com n insuficiente | achados somem no hold-out |
| Intervention Loop | intervenção + desfecho + n viável | apertado | sem desfecho isolável |
| Explainability | cada número tem ficha honesta | com ressalvas | número injustificável |

### Regra de interpretação (essencial)
- **SIGNAL FAILURE** = nenhuma hipótese replica **neste indivíduo**. → A tese **NÃO** está ameaçada. Meu fenótipo pode ser regular demais.
- **PRODUCT THESIS FAILURE** = falha em **Baseline Learnability**, **State Estimation** ou **Explainability** *mesmo com dados adequados*. → Só isso questiona a tese.

Para todo 🔴, distinguir explicitamente:
**(a) ausência real de associação** (n adequado, efeito ~zero, IC estreito) — única que conta contra a tese
**(b) dados insuficientes** (n baixo, IC largo) — problema de coleta
**(c) qualidade inadequada** (buracos, artefatos) — problema de coleta

---

## 8. LIMITAÇÕES A DECLARAR NO OUTPUT

- n=1 não generaliza.
- Prontidão intradiária **não é validável** (não existe verdade-terreno). Toda projeção intradiária é **modelo declarado**, avaliado por plausibilidade — **jamais por acurácia**.
- Sem exames/CGM não há eixo metabólico.
- Confundidores não medidos permanecem (estresse acadêmico, álcool, luz, alimentação).
- **Não interpretar exames laboratoriais clinicamente neste teste.** Nunca.

---

## 9. O QUE FAZER AGORA (nesta ordem)

1. Ler `contexto.md` e os arquivos de dados.
2. **Produzir o relatório de cobertura** e me dizer se o dataset aguenta o protocolo. **Parar aqui e esperar meu OK.**
3. Se OK: baseline adaptativo + state vector + teste de sensibilidade.
4. Próximo Sono (necessidade estimada, janela natural, janela recomendada para amanhã).
5. Tendências + hipóteses sob observação (com FDR e hold-out).
6. Scorecard das 8 dimensões.
7. **A Home manual**, preenchida com dados reais + ficha de metodologia de cada número.
8. Desenho do loop de intervenção para as próximas 3 semanas (uma única intervenção).

**NÃO escrever código de aplicativo. NÃO criar telas. NÃO fazer arquitetura de backend.**
Isto é uma análise, não um produto.

---

## 10. FASE 1 (só depois do Signal Test — não comece)

Se o scorecard vier verde nas dimensões de arquitetura, aí sim discutimos:
Bloco A (ingestão real: HealthKit anchors/background delivery/Oura OAuth), Bloco B (motor estatístico em produção), Bloco C (stack), Bloco D (clinical safety, LGPD/ANVISA, roadmap, negócio).
