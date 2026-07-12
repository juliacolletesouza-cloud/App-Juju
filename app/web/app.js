/* Health Twin — frontend. So RENDERIZA o estado do cerebro (/api/state).
   Zero estatistica aqui. Zero invencao: o que nao da pra dizer, o cerebro marca. */
"use strict";
let STATE=null, TAB="hoje";
const BW=["baixa","moderada","moderada-alta","alta"];
const el=(t,c,h)=>{const e=document.createElement(t);if(c)e.className=c;if(h!=null)e.innerHTML=h;return e;};
const bidx=b=> b==null?-1:BW.indexOf(b);

async function fetchState(){
  for(const u of ["/api/state","data/twin_state.json","data/twin_state.sample.json"]){
    try{const r=await fetch(u,{cache:"no-store"});if(r.ok)return await r.json();}catch(e){}
  }
  return null;
}

/* ---- componentes ---- */
function meter(comp){
  const i=bidx(comp.banda);
  const wrap=el("div","metric");
  const top=el("div","top");
  top.appendChild(el("div","lab",`${comp.rotulo}<small>${comp.fonte}</small>`));
  const val = comp.valor!=null ? `${comp.valor}<em>${comp.unidade||""}</em>` : "—";
  top.appendChild(el("div","val",val));
  wrap.appendChild(top);
  const m=el("div","meter");
  for(let s=0;s<4;s++){
    const on = i>=0 && s===i;
    const ghost = i>=0 && s<i;
    m.appendChild(el("div",`seg b${s} ${on?"on":ghost?"ghost":""}`));
  }
  wrap.appendChild(m);
  if(i>=0){const bw=el("div",`bandword b${i}`,`recuperação ${comp.banda}`);bw.style.marginTop="6px";wrap.appendChild(bw);}
  return wrap;
}

function sparkline(vals,color){
  const v=vals.map(x=>x==null?null:x);
  const nums=v.filter(x=>x!=null);
  if(nums.length<2)return el("div","muted","sem série");
  const min=Math.min(...nums),max=Math.max(...nums),rng=(max-min)||1;
  const W=100,H=30;const n=v.length;
  let d="",started=false;
  v.forEach((x,idx)=>{if(x==null)return;const px=(idx/(n-1))*W;const py=H-((x-min)/rng)*H;
    d+=(started?"L":"M")+px.toFixed(1)+" "+py.toFixed(1)+" ";started=true;});
  const last=v[v.length-1];const lx=W,ly=H-((last-min)/rng)*H;
  const svg=`<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">
    <path d="${d}" stroke="${color}" stroke-width="1.8" fill="none" stroke-linejoin="round" stroke-linecap="round"/>
    <circle cx="${lx}" cy="${ly.toFixed(1)}" r="2.3" fill="${color}"/></svg>`;
  const box=el("div");box.innerHTML=svg;return box.firstChild;
}

function synthesis(){
  // frase composta SO das bandas ja calculadas — reafirma, nao inventa
  const parts=[];
  for(const ss of STATE.substates){
    for(const c of ss.componentes){
      if(c.banda==null)continue;
      const i=bidx(c.banda);
      if(c.rotulo==="FC de repouso") parts.push(i>=2?"FC de repouso baixa pra você":"FC de repouso elevada pro seu normal");
      else if(c.rotulo==="HRV noturna") parts.push(i>=2?"HRV na parte de cima":"HRV na parte de baixo");
      else if(c.rotulo==="Duração") parts.push(i>=2?"boa duração de sono":"sono curto");
      else if(c.rotulo==="Eficiência") parts.push(i<=1?"eficiência baixa (noite picada)":"boa eficiência");
    }
  }
  return parts.length? parts.slice(0,3).join(", ")+"." : "Ainda coletando o suficiente para descrever seu estado.";
}

/* ---- HOJE ---- */
function renderHoje(){
  const v=document.getElementById("view");v.innerHTML="";v.className="fade";
  // hero
  const hero=el("div","card hero");
  hero.appendChild(el("div","date",fmtDate(STATE.noite_ref)));
  hero.appendChild(el("h1","Como você está hoje"));
  hero.appendChild(el("div","synthesis",synthesis()));
  if(STATE.provisorio){
    hero.appendChild(el("div","warn",
      `<span>⚠️</span><span><b>Leitura provisória</b> — base de ${STATE.n_noites} noites. As bandas mudam a cada noite. Não é diagnóstico.</span>`));
  }
  v.appendChild(hero);

  // sub-estados
  const s=el("div","card");
  s.appendChild(el("div","eyebrow","Estado"));
  s.appendChild(el("h2","Sub-estados"));
  s.appendChild(el("p","sub",STATE.nota_estado));
  STATE.substates.forEach(ss=>{
    const box=el("div","substate");box.appendChild(el("div","name",ss.nome));
    ss.componentes.forEach(c=>box.appendChild(meter(c)));
    s.appendChild(box);
  });
  const why=el("details","why");why.appendChild(el("summary",null,"Por que estou vendo isso?"));
  why.appendChild(el("p",null,`Cada barra é a <b>posição do valor de hoje na sua própria distribuição</b> das ${STATE.n_noites} noites. Sem número único — o Signal Test mostrou que um "score" seria instável demais. Barra cheia à direita = recuperação alta.`));
  s.appendChild(why);
  v.appendChild(s);

  // trend sparklines
  if(STATE.trend){
    const row=el("div","spark-row");
    const mk=(cap,arr,color,unit)=>{const b=el("div","spark");
      const last=arr.filter(x=>x!=null).slice(-1)[0];
      b.appendChild(el("div","cap",`<span>${cap}</span><b>${last!=null?last+unit:"—"}</b>`));
      b.appendChild(sparkline(arr,color));return b;};
    row.appendChild(mk("FC repouso (noites)",STATE.trend.rhr,getCss("--accent2")," bpm"));
    row.appendChild(mk("HRV (noites)",STATE.trend.hrv,getCss("--accent")," ms"));
    v.appendChild(row);
  }

  // proximo sono
  const ps=STATE.proximo_sono;if(ps){const c=el("div","card");
    c.appendChild(el("div","eyebrow","Próximo sono"));c.appendChild(el("h2","Sua janela"));
    if(ps.janela_realista)c.appendChild(el("p","sub",`Horário realista de dormir: <b>${ps.janela_realista.mediana}</b> (habitual ${ps.janela_realista.inicio}–${ps.janela_realista.fim}).`));
    if(ps.regularidade_midsleep_min!=null)c.appendChild(el("div","muted",`Regularidade do meio do sono: ±${ps.regularidade_midsleep_min} min.`));
    v.appendChild(c);}

  // capacidades — o "coletando / pronto em X"
  const cap=el("div","card");
  cap.appendChild(el("div","eyebrow","O cérebro está aprendendo"));
  cap.appendChild(el("h2","O que já dá e o que falta"));
  cap.appendChild(el("p","sub","Honesto por princípio: só falo quando os dados aguentam. Enquanto não, mostro quanto falta."));
  STATE.capacidades.forEach(c=>{
    const row=el("div","cap");
    const pct=Math.round((c.pct||0)*100);
    if(c.status==="bloqueado"){row.appendChild(el("div","ring","<span>—</span>"));}
    else{const r=el("div","ring",`<span>${pct}%</span>`);r.style.setProperty("--p",pct);row.appendChild(r);}
    const body=el("div","body");
    body.appendChild(el("div","cname",c.nome));
    body.appendChild(el("div","cmsg", c.status==="pronto" ? ("Pronto — "+(c.desbloqueia||"")) : (c.mensagem||"")));
    row.appendChild(body);
    row.appendChild(el("div",`badge ${c.status}`,c.status));
    cap.appendChild(row);
  });
  v.appendChild(cap);
}

/* ---- HISTORIA ---- */
function renderHistoria(){
  const v=document.getElementById("view");v.innerHTML="";v.className="fade";
  const c=el("div","card");
  c.appendChild(el("div","eyebrow","Longitudinal"));c.appendChild(el("h2","Minha história"));
  c.appendChild(el("p","sub","Janela de rastreio atual, com proveniência. O histórico antigo de treino fica guardado, mas a tela foca no período ativo."));
  const tl=el("div","tl");
  STATE.timeline.slice().reverse().forEach(t=>{
    const it=el("div","tl-item "+(t.tipo||"noite"));
    it.appendChild(el("div","tl-date",fmtDate(t.date)+(t.fonte?" · "+t.fonte:"")));
    if(t.tipo==="ciclo"){it.appendChild(el("div","tl-body",`🩸 ${t.evento||"menstruação"}${t.fim?` (até ${fmtDate(t.fim)})`:""}`));}
    else if(t.tipo==="treino"){it.appendChild(el("div","tl-body",`🏃 Treino${t.wtype?` · ${t.wtype}`:""}`));
      const cw=el("div","chips");if(t.dur_min)cw.appendChild(el("span","chip",`${Math.round(t.dur_min)} min`));if(t.kcal)cw.appendChild(el("span","chip",`${Math.round(t.kcal)} kcal`));it.appendChild(cw);}
    else if(t.tipo==="registro"){it.appendChild(el("div","tl-body",`📝 ${t.texto||""}`));}
    else{it.appendChild(el("div","tl-body","Noite de sono"));
      const cw=el("div","chips");
      if(t.rhr!=null)cw.appendChild(el("span","chip",`FC rep ${t.rhr}`));
      if(t.hrv!=null)cw.appendChild(el("span","chip",`HRV ${t.hrv}`));
      if(t.dur_h!=null)cw.appendChild(el("span","chip",`sono ${t.dur_h}h`));
      if(t.eff!=null)cw.appendChild(el("span","chip",`efic ${t.eff}%`));
      if(t.bedtime)cw.appendChild(el("span","chip",`deitou ${t.bedtime}`));
      it.appendChild(cw);}
    tl.appendChild(it);
  });
  c.appendChild(tl);v.appendChild(c);
}

/* ---- PERGUNTAR ---- */
function renderPerguntar(){
  const v=document.getElementById("view");v.innerHTML="";v.className="fade";
  const add=el("div","card");
  add.appendChild(el("div","eyebrow","Registrar"));add.appendChild(el("h2","Adicionar à minha história"));
  add.appendChild(el("p","sub","Exame, sintoma, evento. Vira memória na timeline — nunca interpretação clínica."));
  const fab=el("button","add","<span class='plus'>+</span> Registrar algo (ex.: “tomei ferro”, “dor de cabeça”)");
  fab.onclick=async()=>{const t=prompt("O que registrar? (fica na sua timeline, sem interpretação)");if(!t)return;
    try{await fetch("/api/event",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({texto:t})});}catch(e){}
    alert("Registrado: “"+t+"”");refresh();};
  add.appendChild(fab);v.appendChild(add);

  const ask=el("div","card");
  ask.appendChild(el("div","eyebrow","Perguntar"));ask.appendChild(el("h2","Perguntar aos meus dados"));
  ask.appendChild(el("p","sub","Responde só com o que está nos SEUS dados. Não dá conselho médico e diz “não sei” quando não sabe."));
  const row=el("div","ask-row");const inp=el("input");inp.placeholder="ex.: qual meu HRV? como dormi?";
  const btn=el("button",null,"Perguntar");row.appendChild(inp);row.appendChild(btn);ask.appendChild(row);
  const out=el("div");ask.appendChild(out);
  const go=()=>{out.innerHTML="";out.appendChild(el("div","answer",answer(inp.value)));};
  btn.onclick=go;inp.addEventListener("keydown",e=>{if(e.key==="Enter")go();});
  v.appendChild(ask);
}
function answer(q){
  q=(q||"").toLowerCase();const find=n=>{for(const s of STATE.substates)for(const c of s.componentes)if(c.rotulo.toLowerCase().includes(n))return c;return null;};
  if(/hrv/.test(q)){const c=find("hrv");return c?`Sua HRV noturna em ${fmtDate(STATE.noite_ref)}: <b>${c.valor} ms</b> — banda ${c.banda}. Fonte: Oura.`:"Sem HRV.";}
  if(/repouso|batim|cora|fc/.test(q)){const c=find("repouso");return c?`FC de repouso: <b>${c.valor} bpm</b> — banda ${c.banda} (baixa pra você = bom). Fonte: Oura.`:"Sem dado.";}
  if(/dorm|sono|efici|dura|deit/.test(q)){const d=find("dura"),e=find("efici"),j=STATE.proximo_sono&&STATE.proximo_sono.janela_realista;
    return `Última noite: duração <b>${d?d.valor+"h":"—"}</b>, eficiência <b>${e?e.valor+"%":"—"}</b>. Janela realista de dormir: <b>${j?j.mediana:"—"}</b>.`;}
  if(/janela|acord|despert|natural/.test(q))return `Janela natural de despertar: <b>não sei</b> — preciso de dias sem despertador. Não vou inventar.`;
  if(/pront|estado|score|energia|como.*est/.test(q))return `Não existe um número único de prontidão (decisão do Signal Test). Veja a aba <b>Hoje</b>: bandas por sub-estado. Base de ${STATE.n_noites} noites — provisório.`;
  if(/recomend|fazer|conselho|dica/.test(q)){const rec=STATE.capacidades.find(c=>c.key==="recomendacoes");
    return rec&&rec.status!=="pronto"?`Ainda não recomendo: ${rec.mensagem} Recomendar agora seria inventar.`:"Veja a aba Hoje.";}
  return `Só respondo com os seus dados. Tente: “meu HRV”, “como dormi”, “FC de repouso”, “janela de dormir”. Conselho clínico é com médico — este app não interpreta.`;
}

/* ---- util ---- */
function fmtDate(d){if(!d)return"";const[y,m,day]=d.split("-");const M=["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"];return`${+day} ${M[+m-1]} ${y}`;}
function getCss(v){return getComputedStyle(document.documentElement).getPropertyValue(v).trim();}
function setTab(name){TAB=name;document.querySelectorAll(".tabs button").forEach(b=>b.classList.toggle("active",b.dataset.tab===name));
  ({hoje:renderHoje,historia:renderHistoria,perguntar:renderPerguntar})[name]();}
document.querySelectorAll(".tabs button").forEach(b=>b.onclick=()=>setTab(b.dataset.tab));

async function refresh(){
  const s=await fetchState();if(!s)return;STATE=s;
  const prov=document.getElementById("prov");
  prov.innerHTML=`<span class="live-dot"></span>${s.fonte_primaria||"—"} · ${s.n_noites||0} noites`;
  setTab(TAB);
}
(async function(){
  STATE=await fetchState();
  if(!STATE){document.getElementById("view").innerHTML='<div class="card">Sem dados. Rode o servidor: <code>python3 backend/server.py</code>.</div>';return;}
  document.getElementById("prov").innerHTML=`<span class="live-dot"></span>${STATE.fonte_primaria} · ${STATE.n_noites} noites`;
  setTab("hoje");
  setInterval(refresh,60000); // atualiza sozinho conforme novos dados chegam
})();
