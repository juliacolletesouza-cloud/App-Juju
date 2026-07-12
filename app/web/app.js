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

  // radar do normal (deteccao de desvio — NAO diagnostico)
  const a=STATE.anomalia;
  if(a && a.status!=="coletando"){
    const fora=a.status==="fora_do_normal";
    const c=el("div","card");
    c.style.borderColor = fora ? "color-mix(in srgb,var(--b2) 45%,var(--line))" : "var(--line)";
    c.appendChild(el("div","eyebrow","Radar do seu normal"));
    const head=el("div","action");
    head.appendChild(el("div","ic", fora?"!":"✓"));
    head.appendChild(el("div","txt",`<b>${a.titulo}</b>`));
    c.appendChild(head);
    if(fora && a.sinais.length){
      const cw=el("div","chips");
      a.sinais.forEach(s=>cw.appendChild(el("span","chip",`${s.rotulo}${s.z?` (${s.z>0?'+':''}${s.z}σ)`:""}`)));
      c.appendChild(cw);
    }
    c.appendChild(el("p","muted",a.mensagem));
    const dz=el("p","muted",a.disclaimer);dz.style.marginTop="6px";dz.style.fontWeight="600";c.appendChild(dz);
    if(a.provisorio)c.appendChild(el("div","muted","<small>Baseline ainda provisório — fica mais confiável com mais noites.</small>"));
    v.appendChild(c);
  }

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
    if(c.status==="bloqueado"||c.status==="limitado"){row.appendChild(el("div","ring","<span>—</span>"));}
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

/* ---- DICAS ---- */
function renderDicas(){
  const v=document.getElementById("view");v.innerHTML="";v.className="fade";
  const d=STATE.dicas;
  if(!d){v.appendChild(el("div","card","Sem dicas ainda."));return;}

  // 1) experimento ativo — a acao real de hoje
  const ex=d.experimento;const c1=el("div","card");
  c1.appendChild(el("div","eyebrow","Hoje, faça isto"));
  c1.appendChild(el("h2",ex.titulo));
  const act=el("div","action");act.appendChild(el("div","ic","✓"));
  act.appendChild(el("div","txt",`<b>${ex.acao}</b>`));c1.appendChild(act);
  const tagline=el("div","muted");tagline.style.marginTop="10px";tagline.innerHTML=`<span class="tag">${ex.rotulo}</span>`;c1.appendChild(tagline);
  const why=el("details","why");why.appendChild(el("summary",null,"Por que só isto?"));
  why.appendChild(el("p",null,ex.porque));c1.appendChild(why);
  v.appendChild(c1);

  // 2) dicas personalizadas — coletando (honesto)
  const p=d.personalizadas;const c2=el("div","card");
  c2.appendChild(el("div","eyebrow","Dicas personalizadas"));
  const row=el("div","cap");
  const r=el("div","ring",`<span>${p.eta?"⏳":"—"}</span>`);r.style.setProperty("--p",0);row.appendChild(r);
  const body=el("div","body");
  body.appendChild(el("div","cname", p.status==="pronto"?"Prontas":"Ainda coletando"));
  body.appendChild(el("div","cmsg", p.status==="pronto"? p.explicacao : (p.mensagem||"")));
  row.appendChild(body);row.appendChild(el("div",`badge ${p.status}`,p.status));
  c2.appendChild(row);
  c2.appendChild(el("p","muted",p.explicacao));
  v.appendChild(c2);

  // 3) dicas gerais — claramente NAO personalizadas
  const c3=el("div","card");
  c3.appendChild(el("div","eyebrow","Dicas gerais"));
  c3.appendChild(el("h2","Higiene do sono"));
  c3.appendChild(el("p","sub",d.gerais_nota));
  d.gerais.forEach(g=>{const it=el("div","substate");
    it.appendChild(el("div","name",g.t));
    it.appendChild(el("div","muted",g.d));c3.appendChild(it);});
  v.appendChild(c3);
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
    else if(t.tipo==="exame"){it.appendChild(el("div","tl-body",`🩸 Exame · ${t.exame||""} ${t.valor||""} ${t.unidade||""}`));}
    else if(t.tipo==="refeicao"){it.appendChild(el("div","tl-body",`🍽️ Refeição${t.nota?` · ${t.nota}`:""}`));}
    else if(t.tipo==="medicacao"){it.appendChild(el("div","tl-body",`💊 ${t.nome||""}${t.dose?` · ${t.dose}`:""}${t.quando?` · ${t.quando}`:""}`));}
    else if(t.tipo==="habito"){it.appendChild(el("div","tl-body",`🎯 Hábito · ${t.texto||""}`));}
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

/* ---- MENU LATERAL (drawer estilo Oura) + folhas ---- */
const ICON={
  perfil:'<circle cx="12" cy="8" r="4"/><path d="M5 20a7 7 0 0 1 14 0"/>',
  disp:'<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/>',
  trend:'<path d="M4 16l5-5 3 3 6-7"/><path d="M15 7h4v4"/>',
  report:'<path d="M6 20V10M12 20V4M18 20v-7"/>',
  integ:'<circle cx="9" cy="9" r="5"/><circle cx="15" cy="15" r="5"/>',
  sobre:'<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
  sangue:'<path d="M12 3s6 7 6 11a6 6 0 0 1-12 0c0-4 6-11 6-11z"/>',
  refeicao:'<path d="M5 3v8M8 3v8M5 11h3M6.5 11v10M17 3c-2 0-3 2-3 5s1 4 3 4v9"/>',
  pilula:'<rect x="3" y="9" width="18" height="6" rx="3"/><path d="M12 9v6"/>',
  coracao:'<path d="M12 20s-7-4.5-9.5-9C1 8 3 4.5 6.5 4.5c2 0 3.5 1.5 5.5 3 2-1.5 3.5-3 5.5-3C21 4.5 23 8 21.5 11c-2.5 4.5-9.5 9-9.5 9z"/>',
  ciclo:'<circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/>',
  plano:'<path d="M9 11l3 3 8-8"/><path d="M20 12v6a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h9"/>',
};
function svg(p){return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">${p}</svg>`;}

function buildChrome(){
  const bar=document.querySelector(".topbar");
  if(bar && !bar.querySelector(".hamb")){
    const h=el("button","hamb");h.setAttribute("aria-label","Menu");
    h.innerHTML=svg('<path d="M4 7h16M4 12h16M4 17h16"/>');
    h.onclick=()=>toggleDrawer(true);
    const left=el("div","left");const brand=bar.querySelector(".brand");
    bar.insertBefore(left,bar.firstChild);left.appendChild(h);left.appendChild(brand);
  }
  if(document.querySelector(".drawer"))return;
  const scrim=el("div","scrim");scrim.onclick=()=>toggleDrawer(false);document.body.appendChild(scrim);
  const dr=el("div","drawer");
  const items=[
    {ic:"perfil",lab:"O meu perfil",sub:"resumo dos meus dados",fn:sheetPerfil},
    {ic:"disp",lab:"Os meus dispositivos",sub:"fontes conectadas",fn:sheetDispositivos},
    {head:"Registrar"},
    {ic:"sangue",lab:"Exames de sangue",sub:"vira memória, sem diagnóstico",fn:sheetExame},
    {ic:"refeicao",lab:"Foto da refeição",sub:"memória visual, sem análise",fn:sheetRefeicao},
    {ic:"pilula",lab:"Medicamentos e suplementos",sub:"efeito fica sob observação",fn:sheetMedicacao},
    {head:"Painéis"},
    {ic:"coracao",lab:"Saúde cardiovascular",sub:"sinais e tendências",fn:sheetCardio},
    {ic:"ciclo",lab:"Ciclo & performance",sub:"covariável, não insight",fn:sheetCiclo},
    {ic:"trend",lab:"Tendências subclínicas",sub:"desvio, não doença",fn:sheetSubclinico},
    {ic:"report",lab:"Recomendações práticas",sub:"o que fazer hoje",fn:()=>{toggleDrawer(false);setTab("dicas");}},
    {head:"Plano"},
    {ic:"plano",lab:"Plano de novos hábitos",sub:"construir com você",fn:sheetPlano},
    {div:true},
    {ic:"integ",lab:"Integrações",sub:"Oura · Apple Watch",fn:sheetIntegracoes},
    {ic:"sobre",lab:"Sobre o Health Twin",fn:sheetSobre},
  ];
  let html=`<div class="wordmark"><span class="macron">HEALTH</span> TWIN</div>`;
  dr.innerHTML=html;
  items.forEach(it=>{
    if(it.div){dr.appendChild(el("div","drawer-div"));return;}
    if(it.head){dr.appendChild(el("div","drawer-head",it.head));return;}
    const b=el("button","drawer-item");
    b.innerHTML=`${svg(ICON[it.ic])}<span class="lab">${it.lab}${it.sub?`<small>${it.sub}</small>`:""}</span>`;
    b.onclick=()=>{it.fn();};
    dr.appendChild(b);
  });
  document.body.appendChild(dr);
  // sheet host
  const ss=el("div","sheet-scrim");ss.onclick=()=>closeSheet();document.body.appendChild(ss);
  const sh=el("div","sheet");document.body.appendChild(sh);
}
function toggleDrawer(open){document.querySelector(".drawer").classList.toggle("open",open);
  document.querySelector(".scrim").classList.toggle("open",open);}
function openSheet(title,builder){
  toggleDrawer(false);
  const sh=document.querySelector(".sheet");sh.innerHTML="";
  sh.appendChild(el("div","grip"));sh.appendChild(el("h3",null,title));
  builder(sh);
  document.querySelector(".sheet-scrim").classList.add("open");sh.classList.add("open");
}
function closeSheet(){document.querySelector(".sheet").classList.remove("open");
  document.querySelector(".sheet-scrim").classList.remove("open");}
function line(host,k,v){const l=el("div","line");l.appendChild(el("div","k",k));l.appendChild(el("div","v",v));host.appendChild(l);}

function sheetPerfil(){openSheet("O meu perfil",h=>{
  const f=STATE.fontes||{};
  line(h,"Noite de referência",fmtDate(STATE.noite_ref));
  line(h,"Noites analisadas",STATE.n_noites);
  Object.entries(f).forEach(([k,v])=>line(h,k,v));
  line(h,"Leitura",STATE.provisorio?"provisória":"consolidada");
  h.appendChild(el("p",null,"n=1: tudo aqui é sobre você, não serve de regra pra outras pessoas."));
});}
function sheetDispositivos(){openSheet("Os meus dispositivos",h=>{
  line(h,"Oura","recuperação e sono · primária");
  line(h,"Apple Watch","treino ("+((STATE.fontes||{})["Apple Watch (treino)"]||0)+" registros)");
  h.appendChild(el("p",null,"Hoje os dados entram por export. A conexão automática (Oura via API) é o próximo passo — aí o app atualiza sozinho após cada sincronização do anel."));
});}
function sheetRelatorio(){openSheet("Relatório do Signal Test",h=>{
  (STATE.limitacoes||[]).forEach(l=>{const p=el("p",null,"• "+l);p.style.margin="8px 0 0";h.appendChild(p);});
  h.appendChild(el("p",null,"Nenhuma hipótese replicou ainda (base curta) — por isso as recomendações aparecem como “coletando”, não como fato. O método completo está no repositório."));
});}
function sheetIntegracoes(){openSheet("Integrações",h=>{
  line(h,"Oura","conectada (export)");
  line(h,"Apple Watch","treino (export)");
  line(h,"Automático (tempo quase real)","próximo passo");
  const est=(STATE.capacidades||[]).find(c=>c.key==="estresse");
  if(est)h.appendChild(el("p",null,est.mensagem));
});}
function sheetSobre(){openSheet("Sobre o Health Twin",h=>{
  h.appendChild(el("p",null,"Um cérebro longitudinal que aprende os seus padrões e diz o que importa — com honestidade acima de tudo."));
  h.appendChild(el("p",null,"• Sem número único de prontidão (o estado é instável demais pra virar um “score”)."));
  h.appendChild(el("p",null,"• Só fala quando os dados aguentam; senão, mostra quanto falta."));
  h.appendChild(el("p",null,"• Detecta desvio do seu normal, mas não diagnostica doença. Isso é com o médico."));
});}

/* ---- ingestão (registra na timeline; NUNCA interpreta) ---- */
function addEvent(kind,payload){
  const date=(payload && payload.data) || todayISO();
  try{fetch("/api/event",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({kind,payload,date})}).catch(()=>{});}catch(e){}
  // otimista: aparece na timeline na hora (demo sem servidor também mostra)
  STATE.timeline.push(Object.assign({date,tipo:kind},payload));
}
function field(host,label,ph,type){
  const w=el("div");w.style.margin="12px 0 0";
  w.appendChild(el("label","sheet-lab",label));
  const i=el("input");i.placeholder=ph||"";if(type)i.type=type;i.className="sheet-inp";
  w.appendChild(i);host.appendChild(w);return i;
}
function saveBtn(host,onSave){
  const b=el("button","sheet-save","Salvar na minha história");
  b.onclick=onSave;host.appendChild(b);return b;
}
function disclaimer(host,txt){const d=el("p","sheet-disc",txt);host.appendChild(d);}

function sheetExame(){openSheet("Registrar exame de sangue",h=>{
  const nome=field(h,"Exame","ex.: Ferritina");
  const val=field(h,"Valor","ex.: 18");
  const un=field(h,"Unidade","ex.: ng/mL");
  const dt=field(h,"Data da coleta","",'date');
  saveBtn(h,()=>{if(!nome.value)return;
    addEvent("exame",{exame:nome.value,valor:val.value,unidade:un.value,data:dt.value||todayISO()});
    closeSheet();toast("Exame registrado na sua história.");});
  disclaimer(h,"Fica como memória e contexto na timeline. O app NÃO interpreta exames clinicamente — isso é com o seu médico. (Regra do projeto.)");
});}
function sheetRefeicao(){openSheet("Foto da refeição",h=>{
  const inp=el("input");inp.type="file";inp.accept="image/*";inp.className="sheet-inp";inp.style.padding="10px";
  h.appendChild(el("label","sheet-lab","Foto"));h.appendChild(inp);
  const nota=field(h,"Nota (opcional)","ex.: almoço, salada + frango");
  saveBtn(h,()=>{const nome=inp.files&&inp.files[0]?inp.files[0].name:"foto";
    addEvent("refeicao",{arquivo:nome,nota:nota.value});closeSheet();toast("Refeição registrada.");});
  disclaimer(h,"Vira memória visual na timeline. O app NÃO calcula calorias nem nutrientes — estimar isso de uma foto seria inventar precisão.");
});}
function sheetMedicacao(){openSheet("Medicamentos e suplementos",h=>{
  const nome=field(h,"Nome","ex.: Vitamina D");
  const dose=field(h,"Dose","ex.: 2000 UI");
  const quando=field(h,"Quando","ex.: manhã, diário");
  saveBtn(h,()=>{if(!nome.value)return;
    addEvent("medicacao",{nome:nome.value,dose:dose.value,quando:quando.value});
    closeSheet();toast("Registrado na sua história.");});
  disclaimer(h,"Entra na timeline como contexto. Qualquer EFEITO na sua recuperação fica “sob observação” — só vira achado quando replicar nos seus dados, nunca por suposição.");
});}

function sheetCardio(){openSheet("Saúde cardiovascular",h=>{
  const find=n=>{for(const s of STATE.substates)for(const c of s.componentes)if(c.rotulo.toLowerCase().includes(n))return c;return null;};
  const rhr=find("repouso"),hrv=find("hrv"),resp=find("resp");
  if(rhr)line(h,"FC de repouso (última noite)",`${rhr.valor} bpm · ${rhr.banda}`);
  if(hrv)line(h,"HRV noturna",`${hrv.valor} ms · ${hrv.banda}`);
  if(resp)line(h,"Freq. respiratória",`${resp.valor} rpm · ${resp.banda}`);
  const t=STATE.trend;if(t){const rr=t.rhr.filter(x=>x!=null);
    line(h,"FC repouso — faixa nas noites",`${Math.min(...rr)}–${Math.max(...rr)} bpm`);}
  const a=STATE.anomalia;if(a&&a.titulo)line(h,"Radar de desvio",a.titulo);
  disclaimer(h,"Painel dos seus sinais cardiovasculares e tendências — NÃO é uma avaliação cardíaca clínica. Sintomas ou dúvidas: procure um cardiologista.");
});}
function sheetCiclo(){openSheet("Ciclo & performance",h=>{
  const ciclos=(STATE.timeline||[]).filter(t=>t.tipo==="ciclo").sort((a,b)=>b.date<a.date?-1:1);
  if(ciclos.length){ciclos.slice(0,6).forEach(c=>line(h,"Menstruação",fmtDate(c.date)+(c.fim?` – ${fmtDate(c.fim)}`:"")));}
  else h.appendChild(el("p",null,"Nenhuma data de ciclo registrada ainda."));
  const cap=(STATE.capacidades||[]).find(c=>c.key==="ciclo");
  if(cap)h.appendChild(el("p",null,"Efeito do ciclo na sua recuperação: "+(cap.mensagem||"coletando")+"" ));
  disclaimer(h,"A fase do ciclo entra como COVARIÁVEL de controle (não vira insight). Seus ciclos são irregulares, então o efeito exige as datas reais e mais tempo. Ciclos muito curtos/longos são assunto de médico.");
});}
function sheetSubclinico(){openSheet("Tendências subclínicas",h=>{
  const a=STATE.anomalia;
  if(a){line(h,"Hoje vs seu normal",a.titulo||"—");
    if(a.sinais&&a.sinais.length)a.sinais.forEach(s=>line(h,s.rotulo,(s.z?`${s.z>0?'+':''}${s.z}σ`:"fora da faixa")));}
  const cap=(STATE.capacidades||[]).find(c=>c.key==="anomalia");
  if(cap&&cap.status!=="pronto")h.appendChild(el("p",null,cap.mensagem));
  disclaimer(h,"Detecção de DESVIO do seu padrão (ex.: FC/temperatura subindo antes de você sentir) — não é diagnóstico de doença. Fica confiável com baseline maior.");
});}
function sheetPlano(){openSheet("Plano de novos hábitos",h=>{
  h.appendChild(el("p",null,"Vamos construir juntas — <b>um hábito por vez</b>, com desfecho medível. É assim que o loop aprende (e é o diferencial do app)."));
  const ex=STATE.dicas&&STATE.dicas.experimento;
  if(ex){const c=el("div","plano-hab");
    c.innerHTML=`<div class="ph-num">1</div><div><b>${ex.titulo}</b><div class="muted">${ex.acao} — em teste 3 semanas.</div></div>`;
    h.appendChild(c);}
  const nome=field(h,"Adicionar um hábito","ex.: 10 min de luz de manhã");
  saveBtn(h,()=>{if(!nome.value)return;addEvent("habito",{texto:nome.value});
    closeSheet();toast("Hábito adicionado ao plano.");});
  disclaimer(h,"Um de cada vez, de propósito: mudar cinco coisas juntas impede saber o que funcionou. Cada hábito vira um pequeno experimento com a sua recuperação como desfecho.");
});}

function toast(msg){let t=document.querySelector(".toast");if(!t){t=el("div","toast");document.body.appendChild(t);}
  t.textContent=msg;t.classList.add("show");setTimeout(()=>t.classList.remove("show"),2600);
  if(TAB==="historia")setTab("historia");}
function todayISO(){const d=new Date();return d.toISOString().slice(0,10);}

/* ---- util ---- */
function fmtDate(d){if(!d)return"";const[y,m,day]=d.split("-");const M=["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"];return`${+day} ${M[+m-1]} ${y}`;}
function getCss(v){return getComputedStyle(document.documentElement).getPropertyValue(v).trim();}
function setTab(name){TAB=name;document.querySelectorAll(".tabs button").forEach(b=>b.classList.toggle("active",b.dataset.tab===name));
  ({hoje:renderHoje,dicas:renderDicas,historia:renderHistoria,perguntar:renderPerguntar})[name]();}
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
  buildChrome();
  document.getElementById("prov").innerHTML=`<span class="live-dot"></span>${STATE.fonte_primaria} · ${STATE.n_noites} noites`;
  setTab("hoje");
  setInterval(refresh,60000); // atualiza sozinho conforme novos dados chegam
})();
