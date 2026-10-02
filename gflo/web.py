"""Loopback-only read-only observer, suitable for an SSH tunnel."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import urllib.parse

from .observe import Observer

PAGE = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GFLO runs</title><style>
:root{color-scheme:light dark;font:16px system-ui;--muted:#657080;--line:#8886}body{max-width:70rem;margin:2rem auto;padding:0 1rem}h1{margin-bottom:.3rem}p{line-height:1.5}article{border:1px solid var(--line);border-radius:.5rem;padding:1rem;margin:1rem 0;overflow-wrap:anywhere}h2{font-size:1.1rem}pre{white-space:pre-wrap;font-size:.85rem}a{color:light-dark(#174ca0,#98bcff)}.meta{color:light-dark(#485362,#b7c0cf)}summary{cursor:pointer;padding:.5rem 0}#connection{font-weight:600}ul{padding-left:1.3rem}@media(prefers-reduced-motion:no-preference){article{transition:border-color .2s}}
</style><h1>GFLO runs</h1><p class="meta">Local execution · read-only view · newest 100 runs. Controls: <code>gflo cancel ID</code> / <code>gflo resume ID</code>.</p><p id="connection" role="status">Connecting…</p><main id="runs"></main>
<script>
const root=document.querySelector('#runs'), state=document.querySelector('#connection');
function el(tag,text){const e=document.createElement(tag);e.textContent=text;return e}
async function poll(){try{const response=await fetch('/api/runs',{cache:'no-store'});if(!response.ok)throw Error('HTTP '+response.status);const runs=await response.json();
const opened=new Set([...root.querySelectorAll('details[open]')].map(x=>x.dataset.id));root.replaceChildren();
if(!runs.length)root.append(el('p','No runs yet. Start a task with the GFLO CLI.'));
for(const r of runs){const card=el('article','');card.append(el('h2',r.id+' · '+r.status));
card.append(el('p','Phase: '+r.phase+' · attempt '+r.attempts+'/'+r.budget.max_attempts+' · turn limit '+r.budget.max_turns+' per attempt'));
card.append(el('p',r.owner_alive?'Runner alive · heartbeat '+r.heartbeat_age_s+'s ago · last action '+r.action_age_s+'s ago':'Runner inactive'));
if(r.waiting_on_model)card.append(el('p',r.model_slow?'Model response is taking longer than 30s; inference may still be working.':'Waiting for local model response.'));
if(r.message)card.append(el('p',r.message));
const detail=el('details','');detail.dataset.id=r.id;detail.open=opened.has(r.id);detail.append(el('summary','Execution details and evidence'));detail.append(el('pre',JSON.stringify(r.detail||{},null,2)));
const links=el('ul','');for(const name of r.artifacts){const li=el('li',''),a=el('a',name);a.href='/api/runs/'+encodeURIComponent(r.id)+'/artifact?name='+encodeURIComponent(name);li.append(a);links.append(li)}detail.append(links);
const a=el('a','Durable event log (JSON)');a.href='/api/runs/'+encodeURIComponent(r.id)+'/events';detail.append(a);card.append(detail);root.append(card)}
state.textContent='Connected · refreshed '+new Date().toLocaleTimeString();}catch(e){state.textContent='Disconnected — showing last snapshot. '+e.message}finally{setTimeout(poll,2000)}}poll();
</script></html>'''


def server(state, port=8787):
    observer = Observer(state)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            host = self.headers.get('Host', '').split(':')[0]
            if host not in ('127.0.0.1', 'localhost'):
                self.send_error(403, 'Use a loopback URL or SSH tunnel')
                return
            try:
                path = urllib.parse.urlsplit(self.path)
                parts = path.path.strip('/').split('/')
                query = urllib.parse.parse_qs(path.query)
                kind = 'application/json'
                if path.path == '/':
                    data, kind = PAGE, 'text/html'
                elif path.path == '/api/runs':
                    data = json.dumps(observer.status())
                elif len(parts) in (3, 4) and parts[:2] == ['api', 'runs']:
                    run = parts[2]
                    if len(parts) == 3:
                        data = json.dumps(observer.status(run))
                    elif parts[3] == 'events':
                        data = json.dumps(observer.events(run, int(query.get('after', ['0'])[0])))
                    elif parts[3] == 'artifact':
                        data, kind = observer.artifact(run, query.get('name', [''])[0]), 'text/plain'
                    else:
                        raise ValueError('Unknown route')
                else:
                    raise ValueError('Unknown route')
                body = data.encode()
                self.send_response(200)
                self.send_header('Content-Type', kind + '; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Cache-Control', 'no-store')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
                self.end_headers()
                self.wfile.write(body)
            except (ValueError, OSError, KeyError):
                self.send_error(404, 'Run or artifact unavailable')
    return ThreadingHTTPServer(('127.0.0.1', port), Handler)
