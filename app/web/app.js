/* Health Twin — frontend. So RENDERIZA o twin_state.json do cerebro.
   Nenhuma estatistica aqui: bandas, numeros e status vem prontos do Python. */
"use strict";

let STATE = null;

async function loadState(){
  // tenta o estado real; cai pro sample se nao existir (repo publico)
  for(const f of ["data/twin_state.json","data/twin_state.sample.json"]){
    try{ const r = await fetch(f); if(r.ok){ return await r.json(); } }catch(e){}
  }
  return null;
}

function el(tag, cls, html){ const e=document.createElement(tag); if(cls)e.className=cls; if(html!=null)e.innerHTML=html; return e; }
function bandTag(b){ if(!b) return '<span class="pill">sem dado</span>';
  return `<span class="band ${b}" data-b="${b}">${b}</span>`; }

/* ---------------- HOJE ---------------- */
function renderHoje(){
  const v = document.getElementById("view"); v.innerHTML="";
  if(STATE.provisorio){
    v.appendChild(el("div","prov-warn",
      `⚠️ <b>Provisório</b> — base de apenas <b>${STATE.n_noites} noites</b>. As bandas mudam a cada noite nova. Isto não é diagnóstico.`));
  }
  const head = el("div","card");
  head.appendChild(el("h2",null,"Como estou — "+STATE.noite_ref));
  head.appendChild(el("p","sub",STATE.nota_estado));
  STATE.substates.forEach(ss=>{
    const box = el("div","substate");
    box.appendChild(el("div","name",ss.nome));
    ss.componentes.forEach(c=>{
      const m = el("div","metric");
      m.appendChild(el("div","lab",`${c.rotulo}<small>fonte: ${c.fonte}</small>`));
      const val = c.valor!=null ? `${c.valor} ${c.unidade||""}` : "—";
      m.appendChild(el("div","val",`${val} ${bandTag(c.banda)}`));
      box.appendChild(m);
    });
    head.appendChild(box);
  });
  const why = el("details","why");
  why.appendChild(el("summary",null,"Por que estou vendo isso?"));
  why.appendChild(el("p",null,
    `Cada banda é a <b>posição do valor de hoje na sua própria distribuição</b> das ${STATE.n_noites} noites — não uma escala absoluta, e sem número único (decisão do Signal Test: o estado é instável demais para virar um "score"). "Banda alta" = recuperação alta (ex.: FC de repouso baixa = bom).`));
  head.appendChild(why);
  v.appendChild(head);

  // proximo sono
  const ps = STATE.proximo_sono; const s = el("div","card");
  s.appendChild(el("h2",null,"Próximo sono"));
  if(ps.janela_realista){
    s.appendChild(el("p","sub",`Janela realista de dormir: <b>${ps.janela_realista.mediana}</b> (habitual ${ps.janela_realista.inicio}–${ps.janela_realista.fim}).`));
  }
  if(ps.regularidade_midsleep_min!=null){
    s.appendChild(el("p","muted",`Regularidade do meio do sono: ±${ps.regularidade_midsleep_min} min.`));
  }
  s.appendChild(el("p","muted",`Janela natural de despertar: <b>não sei</b> — ${ps.janela_natural_motivo}`));
  v.appendChild(s);

  // acoes hoje
  const a = el("div","card"); a.appendChild(el("h2",null,"O que fazer hoje"));
  STATE.acoes_hoje.forEach(ac=>{
    const row = el("div","action");
    row.appendChild(el("div","dot"));
    const txt = el("div"); txt.appendChild(el("div",null,ac.texto));
    const d = el("details","why"); d.appendChild(el("summary",null,"Por quê?")); d.appendChild(el("p",null,ac.porque));
    txt.appendChild(d); row.appendChild(txt); a.appendChild(row);
  });
  v.appendChild(a);

  // hipoteses sob observacao
  const h = el("div","card"); h.appendChild(el("h2",null,"Hipóteses sob observação"));
  h.appendChild(el("p","sub","Nada aqui é insight ainda — são relações que o cérebro está observando, sem afirmar causa."));
  STATE.hipoteses.forEach(hp=>{
    const row = el("div","metric");
    row.appendChild(el("div","lab",`${hp.nome}<small>${hp.detalhe||""}</small>`));
    const cls = hp.status==="sob observação" ? "pill obs":"pill";
    row.appendChild(el("div","val",`<span class="${cls}">${hp.status}</span>`));
    h.appendChild(row);
  });
  v.appendChild(h);
}

/* ---------------- MINHA HISTORIA ---------------- */
function renderHistoria(){
  const v = document.getElementById("view"); v.innerHTML="";
  const c = el("div","card"); c.appendChild(el("h2",null,"Minha história"));
  c.appendChild(el("p","sub","Timeline longitudinal — dados brutos com proveniência. Ingestão ampla, sem narrativa causal."));
  const tl = el("div","tl");
  STATE.timeline.slice().reverse().forEach(t=>{
    const it = el("div","tl-item"+(t.tipo==="ciclo"?" cycle":""));
    it.appendChild(el("div","tl-date",t.date));
    if(t.tipo==="ciclo"){
      it.appendChild(el("div","tl-body",`🩸 ${t.evento} (até ${t.fim})`));
    }else{
      const chips = [];
      if(t.rhr!=null) chips.push(`FC rep ${t.rhr}`);
      if(t.hrv!=null) chips.push(`HRV ${t.hrv}`);
      if(t.dur_h!=null) chips.push(`sono ${t.dur_h}h`);
      if(t.eff!=null) chips.push(`efic ${t.eff}%`);
      if(t.bedtime) chips.push(`deitou ${t.bedtime}`);
      if(t.temp_dev!=null) chips.push(`temp ${t.temp_dev>0?'+':''}${t.temp_dev}°`);
      it.appendChild(el("div","tl-body","Noite (Oura)"));
      const cw = el("div","chips"); chips.forEach(ch=>cw.appendChild(el("span","chip",ch))); it.appendChild(cw);
    }
    tl.appendChild(it);
  });
  c.appendChild(tl); v.appendChild(c);
}

/* ---------------- PERGUNTAR ---------------- */
function renderPerguntar(){
  const v = document.getElementById("view"); v.innerHTML="";
  const add = el("div","card");
  add.appendChild(el("h2",null,"Registrar um dado"));
  add.appendChild(el("p","sub","Ingestão de dados externos (exame, sintoma, evento). Vira memória na timeline — nunca interpretação clínica."));
  const fab = el("button","add-fab","<b>+</b> Registrar algo (ex.: “tomei ferro”, “dor de cabeça”)");
  fab.onclick=()=>{ const t=prompt("O que registrar? (fica na sua timeline, sem interpretação)"); if(t) alert("Registrado localmente: “"+t+"”.\n(Persistência real entra na ingestão automática — próximo passo.)"); };
  add.appendChild(fab); v.appendChild(add);

  const ask = el("div","card");
  ask.appendChild(el("h2",null,"Perguntar aos meus dados"));
  ask.appendChild(el("p","sub","Responde só com o que está nos SEUS dados (proveniência). Não dá conselho médico e diz “não sei” quando não sabe."));
  const row = el("div","ask-row");
  const inp = el("input"); inp.placeholder="ex.: qual meu HRV? como dormi? janela de dormir?";
  const btn = el("button",null,"Perguntar");
  row.appendChild(inp); row.appendChild(btn); ask.appendChild(row);
  const out = el("div"); ask.appendChild(out);
  const go=()=>{ out.innerHTML=""; out.appendChild(el("div","answer",answer(inp.value))); };
  btn.onclick=go; inp.addEventListener("keydown",e=>{if(e.key==="Enter")go();});
  v.appendChild(ask);
}

// consulta deterministica sobre o proprio estado — sem LLM, sem conselho clinico
function answer(q){
  q=(q||"").toLowerCase();
  const last=STATE.substates;
  const find=(name)=>{ for(const s of last) for(const c of s.componentes) if(c.rotulo.toLowerCase().includes(name)) return c; return null; };
  if(/hrv/.test(q)){ const c=find("hrv"); return c?`Sua HRV noturna mais recente (${STATE.noite_ref}) foi <b>${c.valor} ms</b> — banda ${c.banda} na sua distribuição. Fonte: Oura.`:"Não tenho HRV recente."; }
  if(/repouso|fc|cora|batim/.test(q)){ const c=find("repouso"); return c?`FC de repouso mais recente: <b>${c.valor} bpm</b> — banda ${c.banda} (baixa pra você = bom). Fonte: Oura.`:"Sem dado."; }
  if(/dorm|sono|deit|efici|dura/.test(q)){ const d=find("dura"),e=find("efici"),j=STATE.proximo_sono.janela_realista;
    return `Última noite: duração <b>${d?d.valor+'h':'—'}</b> (banda ${d?d.banda:'—'}), eficiência <b>${e?e.valor+'%':'—'}</b>. Janela realista de dormir: <b>${j?j.mediana:'—'}</b>.`; }
  if(/janela|acord|despert|natural/.test(q)){ return `Janela natural de despertar: <b>não sei</b> — precisa de dias sem despertador, que ainda não tenho. Não vou inventar.`; }
  if(/pront|estado|como.*est|score|energia/.test(q)){ return `Não existe um número único de prontidão (decisão do Signal Test). Veja a aba <b>Hoje</b>: estado por bandas de sub-estado. Base de ${STATE.n_noites} noites — provisório.`; }
  return `Só respondo com o que está nos seus dados. Tente: “meu HRV”, “como dormi”, “janela de dormir”, “FC de repouso”. Para conselho clínico, procure um médico — este app não interpreta.`;
}

/* ---------------- tabs ---------------- */
function setTab(name){
  document.querySelectorAll(".tabs button").forEach(b=>b.classList.toggle("active",b.dataset.tab===name));
  ({hoje:renderHoje,historia:renderHistoria,perguntar:renderPerguntar})[name]();
}
document.querySelectorAll(".tabs button").forEach(b=>b.onclick=()=>setTab(b.dataset.tab));

(async function(){
  STATE = await loadState();
  const prov = document.getElementById("prov");
  if(!STATE){ document.getElementById("view").innerHTML='<div class="card">Sem <code>twin_state.json</code>. Rode o cérebro: <code>python3 app/brain/build_state.py</code>.</div>'; return; }
  prov.textContent = `${STATE.fonte_primaria} · ${STATE.n_noites} noites · ${STATE.gerado_em}`;
  setTab("hoje");
})();
