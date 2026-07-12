# Pré-registro da análise da intervenção (âncora de horário de dormir)

> Escrito em **2026-07-12, ANTES de coletar qualquer dado** das 3 semanas.
> Objetivo: travar todas as decisões analíticas para que o resultado de 2/ago não
> possa ser "escolhido a dedo". Qualquer desvio deste documento será declarado.

## Hipótese (direção pré-especificada)
Noites com início de sono **dentro** da janela âncora (23:00–23:30) têm **FC de
repouso noturna menor** (melhor recuperação) que noites **fora** da janela,
within-person.

## Desfechos
- **Primário:** FC de repouso noturna (Oura), como desvio do baseline móvel.
- **Secundário (exploratório):** HRV noturna (Oura). Não decide nada sozinho.

## Exposição / aderência (definida agora)
- **Aderência da noite** = início de sono (Oura `Bedtime Start`) entre **23:00 e
  23:30**. Binário: dentro / fora.
- **Aderência da semana** = % de noites dentro. Alvo declarado: ≥5/7.

## Janelas
- Semana 1 (13–19/jul) = **baseline**, sem mudança. Semanas 2–3 (20/jul–02/ago) =
  âncora ativa.
- A comparação principal é **dentro vs fora da janela** agregando as 3 semanas
  (dá mais n que comparar semana a semana). A divisão baseline/âncora entra só
  como checagem de que a aderência de fato subiu na fase ativa.

## Teste estatístico (idêntico ao Signal Test)
- Estimador de efeito: diferença de medianas robusta (Hodges–Lehmann) da FC de
  repouso entre noites dentro vs fora.
- Significância: **permutação circular em blocos** (respeita autocorrelação),
  2000 reps, seed=42.
- Incerteza: IC95 por block bootstrap (bloco 7).
- **Sem** correção de múltiplos testes aqui (é 1 desfecho primário). HRV é rotulada
  exploratória.

## Regra de decisão (travada)
- **Sinal preliminar** SE: efeito na direção esperada (RHR menor dentro da janela)
  **E** p_perm < 0,10 **E** IC95 não cruza zero.
- Caso contrário: **"sem sinal neste piloto"** — e isso **NÃO** vira "regularidade
  não importa" (n≈21 não tem poder). Vira hipótese que continua sob observação na
  Oura.
- **n mínimo para sequer reportar efeito:** ≥15 noites com aderência classificável
  e ≥5 noites em cada grupo. Abaixo disso → só relato de aderência, sem inferência.

## Confundidores que serão declarados (não necessariamente ajustados, n permitindo)
- Dia da semana (fim de semana), fase do ciclo (datas reais do `contexto.md`),
  carga de treino do dia. Com n≈21 provavelmente **não** dá para ajustar tudo —
  então serão **reportados como não controlados**, não escondidos.

## O que NÃO vou fazer
- Não trocar a janela âncora depois de ver os dados.
- Não trocar o desfecho primário para a HRV se a RHR não der sinal.
- Não remover noites "inconvenientes" sem uma regra de qualidade pré-dita
  (exclusão só por: sono < 3h registrado, ou não-uso do anel na noite).
