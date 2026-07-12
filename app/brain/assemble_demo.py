import json, re, pathlib
css = pathlib.Path("app/web/styles.css").read_text()
js  = pathlib.Path("app/web/app.js").read_text()
state = json.load(open("/tmp/state.json"))

# 1) fetchState -> retorna estado embutido; sem polling
js = re.sub(r"async function fetchState\(\)\{.*?\n\}",
            "async function fetchState(){ return window.__STATE__; }", js, count=1, flags=re.S)
js = js.replace("  setInterval(refresh,60000); // atualiza sozinho conforme novos dados chegam", "")

topbar = '''<div class="topbar">
  <div class="brand"><span class="glyph">◐</span> Health Twin</div>
  <div class="prov" id="prov"></div>
</div>
<div style="max-width:560px;margin:0 auto;padding:0 16px">
  <div style="font-size:11.5px;color:var(--muted);background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 12px;text-align:center">
    Demo · snapshot dos seus dados reais em 11 jul 2026 · privado
  </div>
</div>'''
nav = '''<nav class="tabs">
  <button data-tab="hoje" class="active"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>Hoje</button>
  <button data-tab="dicas"><svg viewBox="0 0 24 24"><path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10c.7.7 1 1.3 1 2h6c0-.7.3-1.3 1-2a6 6 0 0 0-4-10z"/></svg>Dicas</button>
  <button data-tab="historia"><svg viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h10"/></svg>História</button>
  <button data-tab="perguntar"><svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H8l-4 4V5a2 2 0 0 1 2-2h13a2 2 0 0 1 2 2z"/></svg>Perguntar</button>
</nav>'''

html = f"""<style>
{css}
</style>

{topbar}
<main id="view"></main>
{nav}

<script>window.__STATE__ = {json.dumps(state, ensure_ascii=False)};</script>
<script>
{js}
</script>
"""
pathlib.Path("app/web/demo.html").write_text(html)
print("demo.html:", len(html), "bytes")
