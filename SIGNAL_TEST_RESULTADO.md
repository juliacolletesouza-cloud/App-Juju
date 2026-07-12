# Signal Test — Resultado (Fase 0)

> Julia, este é o entregável final da Fase 0, rodado no **caminho C**: caracterizei
> a janela histórica do **Apple Watch (2024)** e defini a **Oura** como fonte limpa
> do go-forward. Todo número aqui vem de **código determinístico e auditável**
> (`analise/`), não de "achismo" de LLM. Reproduza com `python3 analyze.py` e
> `python3 oura_home.py`.
>
> **Veredito de uma linha:** o cérebro *tem o que aprender* (o pipeline roda ponta
> a ponta em dados reais e o baseline de FC de repouso é aprendível), mas **nenhuma
> hipótese da allowlist se sustentou na janela 2024** — e isso é **falha de coleta/
> qualidade (tipo b/c), não ausência real de sinal (tipo a)**. Pela regra do §7,
> **a tese do produto NÃO está ameaçada.** O teste limpo acontece na Oura, daqui
> pra frente.

---

## 1. O que foi efetivamente analisado

| | Janela usada | n | Papel |
|---|---|---|---|
| **Apple Watch 2024** | 2024-03-05 → 2024-12-28 | 254 dias (250 com RHR+sono) | Teste retrospectivo (fechado — você não usa mais o Watch pra dormir) |
| **Oura** | 2026-06-24 → 2026-07-11 | 18 noites | Home atual + baseline do go-forward |

**Desfecho de recuperação primário = FC de repouso (RHR).** A HRV do Apple Watch é
**amostra pontual (spot), não noturna** — e o baseline dela ficou **indistinguível
de ruído** (§2 abaixo), então entra só como secundária com ressalva. Sono de 2024 é
**iPhone "tempo na cama"** (proxy), não sono estagiado (só 14–15 noites estagiadas).

---

## 2. Baseline Learnability — o baseline é aprendível?

Mediana móvel robusta + MAD (janela crônica 42d). Métrica: razão sinal/ruído =
(amplitude p10–p90 do baseline) ÷ (MAD típico do dia-a-dia).

| Métrica | Amplitude baseline | MAD típico | Razão S/R | Leitura |
|---|---|---|---|---|
| **RHR** | 8,0 bpm | 4,45 bpm | **1,8** | Aprendível, sinal modesto 🟡 |
| **HRV (spot)** | 8,5 ms | 8,97 ms | **0,94** | Ruído ≈ sinal — **não baseia** 🔴 |

**Conclusão:** RHR é o eixo de recuperação que dá pra aprender nesta janela. A HRV
spot do Apple Watch **não serve de baseline** (é o motivo de a Oura, com HRV
noturna real, ser a fonte certa daqui pra frente).

---

## 3. State Estimation — teste de sensibilidade do estado (§6)

Sintetizei os sub-estados (em percentil da própria distribuição) num "battery" por
**5 especificações** e medi a **taxa de troca de banda** entre elas.

**Taxa de troca média entre especificações = 0,623 (62%).**
Critério do protocolo: estável se **< 0,15–0,20**. Todos os pares ficaram entre
**0,29 e 0,74**.

➡️ **Decisão pré-registrada do §6 acionada:** como nenhuma spec fica abaixo de
~15–20%, **a resposta é a candidata 5 — "sem escalar"**. **O produto NÃO deve ter
um número/bateria único.** O estado se comunica como **bandas por sub-estado**,
governadas por regras sobre o vetor.

**Ressalva honesta:** parte dessa instabilidade é agravada por a janela 2024 ser
*pobre de vetor* (HRV é ruído; sem temperatura; sem ciclo), o que deixa o
sub-estado autonômico quase que só-RHR. Ou seja, isto é **em parte tipo (b/c)**. A
recomendação "sem escalar" deve ser **reconfirmada na Oura**, onde o vetor é completo.

---

## 4. Associações da allowlist — hold-out + FDR

Within-person, desvio do baseline crônico (remove drift lento). Defasagem correta
(exposição da noite → RHR da manhã; carga do dia D-1 → RHR em D). Theil-Sen + IC por
block bootstrap + p por permutação circular em blocos + **FDR-BH** + **hold-out
temporal 2/3 → 1/3**. Replicação **só conta** se: sinal replica **E** p<0,10 **E** IC
não cruza zero.

| Hipótese | n | slope Theil-Sen | IC95 | p_perm | q_FDR | **Replicação válida** |
|---|---|---|---|---|---|---|
| H1 horário de dormir → RHR | 241 | 0,00 | [−0,027; 0,012] | 1,00 | 1,00 | ❌ |
| H2 irregularidade do sono → RHR | 242 | −0,016 | [−0,090; 0,047] | 0,47 | 1,00 | ❌ (sinal replica, mas IC cruza 0 e p alto → **confundidor, provavelmente fim de semana**) |
| H3 duração do sono → RHR | 227 | 0,00 | [−0,020; 0,010] | 1,00 | 1,00 | ❌ |
| H4 carga de treino D-1 → RHR | 245 | 0,00 | [−0,027; 0,014] | 1,00 | 1,00 | ❌ (sinal replica em efeito ~zero → ruído) |

**Não testáveis nesta janela (declarado, não escondido):**
- **H5 treino noturno → latência/eficiência do sono** — exige sono estagiado; só
  ~15 noites em 2024. *(tipo b/c: coleta.)*
- **H6 fase do ciclo → HRV** — sem datas de menstruação em 2024. *(tipo b: coleta —
  aguarda `contexto.md`.)*

**Interpretação (§7, obrigatória para todo 🔴):** as quatro nulas são **(b) dados
insuficientes em qualidade + (c) medida proxy** — não **(a) ausência real**. Por quê:
o sono é "tempo na cama" do iPhone (erro de medida atenua qualquer efeito real para
zero), a HRV é inutilizável, e os confundizadores obrigatórios (ciclo, doença,
viagem) **não foram aplicados** (faltou `contexto.md`). Logo, **isto NÃO conta
contra a tese.** É SIGNAL FAILURE por coleta — exatamente o cenário que o §7 manda
não confundir com falha de produto.

H2 e H4 (sinal replica, mas sem significância) viram **hipóteses sob observação**
para a Oura — **jamais insight** agora.

---

## 5. Scorecard de viabilidade (8 dimensões independentes)

| Dimensão | Nota | Justificativa |
|---|---|---|
| **Data Coverage** | 🟡 | RHR e timing de sono densos (250 noites), **mas** sono é proxy iPhone, HRV é ruído, sem temperatura. Oura resolve isso adiante. |
| **Baseline Learnability** | 🟡 | RHR aprendível (S/R 1,8); HRV spot não (S/R 0,94). Uma métrica robusta, não todas. |
| **State Estimation** | 🟡 | Vetor ok, **escalar instável (62%)** → produto "sem escalar" (candidata 5). Instabilidade parte de vetor pobre nesta janela (b/c). Reconfirmar na Oura. |
| **Sleep Recommendation** | 🟡 | Dá a **janela realista** (mediana 23:15, IQR 22:35–00:40). **Não dá a janela natural** — precisa de dias sem despertador (`contexto.md`). |
| **Trend Detection** | 🟡 | Ficou corretamente **em silêncio** onde não havia sinal (não viu tendência no ruído). Detecção de tendência real não foi exercida (sem tendência conhecida pra validar). |
| **Hypothesis Replication** | 🔴 **(b/c)** | Nenhuma replica com validade. **Mas é coleta/qualidade, não ausência real** → **não ameaça a tese** (§7). |
| **Intervention Loop** | 🟡 | Loop desenhável e com n viável na Oura (§7 abaixo). Apertado só pela janela curta atual. |
| **Explainability** | 🟢 | Todo número tem ficha de metodologia honesta (§6). Nenhum número injustificável. |

**Nenhuma dimensão de tese de produto (Baseline / State / Explainability) falhou
*com dados adequados*.** Os 🔴/🟡 são dirigidos por coleta. Tradução: **construir vale
a pena; o gargalo é dado, não fenômeno.**

---

## 6. A HOME MANUAL — preenchida com dados reais (Oura, noite de 2026-07-11)

> Bandas = **posição na própria distribuição** das 18 noites (nunca escala
> absoluta). **n=18 ⇒ PROVISÓRIO.** Sem escalar (candidata 5): sub-estados em banda,
> sem número único. "Banda alta" = **recuperação alta**, não valor alto.

### HOJE — como estou
| Sub-estado | Número real | Banda (recuperação) |
|---|---|---|
| Autonômico — HRV noturna | 49 ms | **moderada-alta** (p72) |
| Autonômico — FC repouso | 71,8 bpm | **alta** (p78 — baixa pra ela = bom) |
| Suficiência de sono — duração | 7,74 h | **moderada-alta** (p56) |
| Suficiência de sono — eficiência | 88% | **baixa** (p00 — pior das 18) |
| Freq. respiratória | 17,25 | **alta** (p83 — baixa = bom) |

**Síntese linguística honesta:** *"Recuperação autonômica hoje na parte de cima do
seu normal (FC de repouso baixa, HRV ok). O sono teve duração boa, mas a eficiência
foi a mais baixa das últimas semanas — noite mais picada."* Sem número de dois
dígitos. Sem "prontidão: 82".

### Próximo sono
- **Janela realista de dormir:** mediana **23:15**, faixa habitual **22:35–00:40**.
- **Regularidade:** DP do midsleep = **91 min** (bastante variável — alvo natural de
  intervenção, ver §7).
- **Janela natural de despertar:** **NÃO SEI.** Exige dias sem despertador —
  preciso do `contexto.md`. (Não vou inventar.)

### O que fazer hoje (1–3 ações)
Com n=18 e sem `contexto.md`, a Home ainda **não deve recomendar** com confiança.
A ação honesta de hoje é **coletar** (a intervenção do §7), não prescrever.

---

## 7. Fichas de metodologia (cada número tem origem)

- **Banda (todos):** percentil do valor da noite dentro das 18 noites Oura;
  4 faixas por quartil. Fonte: `oura_home.py`. Limite: n=18, banda instável a ±1
  noite.
- **RHR / HRV / duração / eficiência / freq. resp.:** valores nightly diretos do
  export Oura Trends (fonte primária de sono/recuperação, §4). Sem média entre fontes.
- **Janela realista de dormir:** mediana e IQR do horário de início de sono (Oura),
  convertidos de "minutos após 18:00" para evitar wraparound da meia-noite.
- **Baseline S/R (RHR/HRV):** mediana móvel 42d ± MAD×1,4826, janela Apple Watch
  2024. Fonte: `analyze.py`.
- **Taxa de troca de banda:** média das trocas par-a-par entre 5 specs de síntese,
  bandas por quartil. Fonte: `analyze.py`.
- **Slopes/IC/p/q:** Theil-Sen; IC block bootstrap (bloco 7, 1000 reps); p por
  deslocamento circular (2000 reps); FDR-BH; hold-out 2/3→1/3. Seed=42. Fonte:
  `analyze.py`.

---

## 8. Loop de intervenção — próximas 3 semanas (uma só intervenção)

O achado mais acionável não é uma associação (nenhuma sobreviveu) — é o
**alvo de regularidade**: seu midsleep varia **±91 min**. A literatura de sono liga
irregularidade a pior recuperação, e é a única alavanca com **desfecho isolável** na
Oura já.

- **Intervenção (única):** **âncora de horário de dormir** — deitar dentro de uma
  janela de 30 min ao redor de **23:15** em ≥5 das 7 noites/semana.
- **Aderência (medida):** % de noites com bedtime dentro da janela (Oura, objetivo).
- **Desfecho primário:** FC de repouso noturna (Oura). **Secundário:** HRV noturna.
- **Desenho:** semana 1 = baseline (sem mudar nada); semanas 2–3 = âncora ativa.
  Comparo RHR das noites "dentro da janela" vs "fora" **within-person**, com a mesma
  permutação circular. n viável: ~21 noites → ~15 dentro / ~6 fora (apertado, mas é
  começo; robustece conforme a Oura acumula).
- **Por que só uma:** o loop recomendação→aderência→resposta é o fosso (§2). Testar
  uma alavanca isolável > embaralhar cinco.

---

## 9. Limitações declaradas (§8)

- **n=1 não generaliza.** Nada aqui vira regra populacional.
- **Janela 2024 usa sono proxy (iPhone "na cama")** e **HRV spot** — atenuam efeitos
  reais para zero. As nulas são coleta, não fenômeno.
- **Confundidores obrigatórios não aplicados** (ciclo, doença, viagem) — faltou
  `contexto.md`. H2 (irregularidade) tem cara de **confundida por fim de semana**.
- **Sem temperatura no Apple Watch; sem exames/CGM** → sem eixo metabólico, sem
  desvio de temperatura no state vector de 2024.
- **Prontidão intradiária não é validável** (não foi estimada — sem verdade-terreno).
- **Home atual é n=18** → bandas provisórias, revisar semanalmente.

---

## 10. Próximo passo concreto

1. **`contexto.md`** — me dá (aqui no chat serve): dias sem despertador, datas de
   menstruação, e qualquer doença/viagem/prova no período. Isso destrava a **janela
   natural de despertar** e os **confundidores** (H2/H6).
2. **Rodar a intervenção do §8 por 3 semanas** na Oura.
3. Em ~6–8 semanas de Oura, **repito a allowlist inteira** com HRV noturna real,
   sono estagiado e confundidores — aí sim o teste de sinal *definitivo* deste
   fenótipo.
