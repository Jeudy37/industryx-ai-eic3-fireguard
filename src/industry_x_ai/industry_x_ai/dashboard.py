"""Tableau de bord Web temps réel (serveur HTTP léger, sans dépendance externe)."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HTML = """<!doctype html><html lang="fr"><meta charset="utf-8"><title>INDUSTRY-X AI — Supervision</title>
<style>body{font-family:system-ui,sans-serif;margin:0;background:#0f1b33;color:#e8eefc}
header{background:#1b3a7a;padding:14px 22px;border-bottom:3px solid #f2a50c}h1{margin:0;font-size:20px}
main{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;padding:18px}
.c{background:#16264a;border-radius:10px;padding:14px}.c h2{margin:0 0 6px;font-size:13px;color:#9db4e6;text-transform:uppercase}
.v{font-size:30px;font-weight:700}.ok{color:#5be28a}.bad{color:#ff6b6b}.w{color:#f2a50c}
table{width:100%;border-collapse:collapse;font-size:13px}td,th{padding:4px 6px;border-bottom:1px solid #26407a;text-align:left}
.wide{grid-column:1/-1}</style>
<header><h1>INDUSTRY-X AI — Supervision de la cellule (EIC 3.0 · FIREGUARD-X)</h1></header><main id="m">Chargement…</main>
<script>
const cls=s=>s=='IDLE'?'ok':(s=='BUSY'?'w':'bad');
async function f(){try{const d=await (await fetch('/metrics')).json();const s=d.summary;
const c=(t,v,k='')=>`<div class=c><h2>${t}</h2><div class="v ${k}">${v}</div></div>`;
let h=c('Pièces traitées',s.pieces_processed)+c('Réussites',s.success,'ok')+c('Erreurs',s.errors,s.errors?'bad':'ok')
+c('Taux de réussite',s.success_rate_pct+' %')+c('Temps de cycle moyen',(s.cycle_mean_s??'-')+' s')
+c('Collisions',s.collisions,s.collisions?'bad':'ok')+c('Distance min. bras',(s.min_arm_distance_m??'-')+' m')
+c('Distance actuelle',(d.distance??'-')+' m')
+c('Robot A',`${d.robots.A?.state??'?'}<br><small>${d.robots.A?.task??''}</small>`,cls(d.robots.A?.state))
+c('Robot B',`${d.robots.B?.state??'?'}<br><small>${d.robots.B?.task??''}</small>`,cls(d.robots.B?.state))
+c('Bac A (rouge)',s.per_bin.A)+c('Bac B (vert)',s.per_bin.B)+c('Bac C (bleu)',s.per_bin.C);
h+='<div class="c wide"><h2>Derniers cycles</h2><table><tr><th>#</th><th>Pièce</th><th>Couleur</th><th>Forme</th><th>Bac</th><th>Résultat</th><th>Cycle (s)</th></tr>'
+d.cycles.slice(-10).reverse().map(r=>`<tr><td>${r.cycle}</td><td>${r.piece_id}</td><td>${r.color??''}</td><td>${r.shape??''}</td><td>${r.sorted_bin??'-'}</td><td class="${r.result=='OK'?'ok':'w'}">${r.result}</td><td>${r.cycle_time_s??'-'}</td></tr>`).join('')+'</table></div>';
document.getElementById('m').innerHTML=h}catch(e){}}
f();setInterval(f,1000);</script></html>"""


def start(get_metrics, port=8080):
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/metrics"):
                body, ctype = json.dumps(get_metrics()).encode(), "application/json"
            else:
                body, ctype = HTML.encode(), "text/html; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass
    srv = ThreadingHTTPServer(("0.0.0.0", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
