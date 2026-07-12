# Relatório de Cobertura — Signal Test Fase 0

> Gerado a partir dos arquivos enviados em 2026-07-12.
> **Só contagens e datas agregadas** — nenhum valor bruto de saúde neste arquivo.
> Este é o passo §9.2 do protocolo: **antes de qualquer análise**. Nada foi
> analisado ainda.

## Arquivos recebidos

| Arquivo | O que é | Tamanho |
|---|---|---|
| `oura_20260624_20260719_trends.csv` | Export **"Trends"** da Oura (diário agregado) | 18 noites |
| `exportar.zip` → `exportar.xml` | Apple Health completo | 665 MB, ~2,5 anos |

---

## 1. Oura — o problema nº 1

- **Só 18 noites**: 2026-06-24 → 2026-07-11.
- É o export **"Trends" (diário agregado)** — o próprio protocolo (§3) avisa que
  ele **não tem intradiário** e pede **histórico completo, não 4 semanas**.
- As 18 noites estão **completas e limpas** (HRV noturna, FC repouso, estágios,
  duração, eficiência, timing, desvio de temperatura, freq. respiratória — tudo
  presente em todas as noites). Qualidade boa; **quantidade insuficiente.**

**Pista importante:** dentro do Apple Health, os registros com fonte "Oura"
também começam só em **2026-06-23**. Ou seja, tudo indica que **o anel Oura tem
~3 semanas de uso** — provavelmente **não existe** histórico Oura mais longo para
re-exportar. *(Preciso que você confirme: quando começou a usar o anel?)*

---

## 2. Apple Health — longo, mas com buracos e mudança de aparelho

Span bruto vai de 2022 a 2026-07-12, mas o que **serve para recuperação** é mais
curto e desigual:

| Métrica | Fonte real | Cobertura útil |
|---|---|---|
| **FC intradiária** | Apple Watch | 585 dias com dado (a jóia da coroa — única fonte intradiária) |
| **FC de repouso (RHR)** | Apple Watch | densa em **2024** (~diária), **decai em 2025**, esparsa em 2026 |
| **HRV (SDNN)** | Apple Watch | idem — mas são **amostras pontuais (spot), NÃO HRV noturna média** |
| **Sono estagiado** (Core/Deep/REM) | Watch **22 noites** (2024-03→2025-02) + Oura **19 noites** (2026-06→07) | **~41 noites no total**, em 2 janelas que não se sobrepõem |
| **Sono "na cama" (InBed)** | iPhone | 8.506 registros — **só tempo na cama, sem estágios** |
| **Fluxo menstrual** | — | 9 registros (2026-02 → 2026-06), esparso |

### O padrão que os dados contam
1. **Era Apple Watch (~mar/2024 → início 2025):** RHR quase diária, HRV spot
   densa. **Janela de recuperação mais longa que existe.** Ressalvas: HRV é spot,
   não noturna; sono estagiado só 22 noites.
2. **2025 — degradação:** o uso do Watch despenca (RHR cai de ~24/mês para
   ~7/mês; sono estagiado para de fato após fev/2025). Buraco grande.
3. **Era Oura (24/jun/2026 →):** só ~18 noites, alta fidelidade nightly, n minúsculo.

---

## 3. Confronto com o protocolo

**Source Resolution (§4)** manda: sono, HRV noturna, FC repouso, temperatura →
**Oura primária**. Na prática a Oura tem **18 noites**. Isso:

- fica **abaixo do n mínimo = 20** (§4);
- **inviabiliza** o hold-out temporal 2/3 → 1/3 (§4);
- **inviabiliza** o baseline crônico de janela 28–60d (§4).

A única série longa de recuperação é do **Apple Watch (2024)** — que o protocolo
define como **secundária** e cuja HRV é **spot, não noturna**. Usá-la como
primária é um **desvio de Source Resolution** — decisão sua, não minha, para
tomar de forma explícita.

### Classificação do 🔴 (regra do §7)
Isto é **(b) dados insuficientes + (c) qualidade de coleta** — **NÃO** é
**(a) ausência real de associação**. Pela regra de interpretação do §7, **a tese
do produto NÃO está ameaçada.** É um problema de *coleta*, não de fenômeno.

### Data Coverage (dimensão do scorecard), honesto e dividido
- Recuperação (RHR/HRV) na janela 2024 do Watch: **🟡** (longa, mas HRV é spot e
  há decaimento).
- Sono estagiado: **🔴** (~41 noites em 2 janelas separadas).
- Oura como primária conforme protocolo: **🔴** (18 noites).

---

## 4. Veredito: o dataset **como está** não aguenta o protocolo completo

Não por falta de sinal fisiológico — por **falta de quantidade e por mudança de
aparelho no meio**. Há três caminhos possíveis (decisão sua):

**Caminho A — Coletar antes de rodar.** Se o anel Oura tem ~3 semanas, usar ele
como fonte primária vai de vento em popa **daqui pra frente**. Bastam ~6–8
semanas contínuas de Oura para o Signal Test rodar como desenhado. Mais honesto,
mais lento.

**Caminho B — Signal Test reduzido sobre a janela Apple Watch 2024.** Redesignar
Apple Watch como primária **só nessa janela**, com ressalvas explícitas (HRV
spot, sem temperatura, sono estagiado fraco). Dá pra testar baseline + parte da
allowlist com RHR como desfecho principal. Resultado sai agora, mas com asteriscos.

**Caminho C — Os dois.** Caracterizo já a janela 2024 (baseline + o que a
allowlist permitir com RHR), e trato a Oura como a fonte de alta fidelidade do
go-forward. Combina resultado imediato + coleta limpa.

---

## 5. O que eu preciso de você para decidir

1. **Quando você começou a usar o anel Oura?** (confirma se existe histórico Oura
   para re-exportar ou se são mesmo ~3 semanas).
2. **Você ainda usa o Apple Watch para dormir hoje?** (define se a janela 2026
   pode ser adensada com o Watch enquanto a Oura acumula).
3. **Qual caminho — A, B ou C?**
4. Preencher o **`contexto.md`** (ou me responder no chat): dias sem despertador,
   datas de menstruação, doença/viagem/prova, mudanças de treino/medicação.

**Parei aqui, conforme §9.2. Nenhuma análise rodou. Aguardo sua decisão.**
