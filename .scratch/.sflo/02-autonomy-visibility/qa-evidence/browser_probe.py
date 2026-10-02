import sys, tempfile, threading, json, subprocess, urllib.request
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from gflo.runner import Factory
from gflo.web import server
from playwright.sync_api import sync_playwright
out=Path('.scratch/.sflo/02-autonomy-visibility/qa-evidence')
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp); state=root/'state'; f=Factory(state,lambda *a:{},lambda *a:{'passed':True})
 http=server(state,0); threading.Thread(target=http.serve_forever,daemon=True).start(); port=http.server_port; base=f'http://127.0.0.1:{port}'
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  page=browser.new_page(viewport={'width':1280,'height':800},color_scheme='light'); page.goto(base); page.get_by_text('No runs yet.').wait_for(); page.screenshot(path=str(out/'desktop-empty.png'))
  repo=root/'repo';repo.mkdir();(repo/'app.py').write_text('value=1\n')
  for args in (['init','-q'],['add','.'],['-c','user.name=QA','-c','user.email=qa@local','commit','-qm','base']):subprocess.run(['git','-C',str(repo),*args],check=True)
  a=root/'acceptance';a.mkdir();(a/'check.py').write_text('assert True')
  task=root/'task.json';task.write_text(json.dumps(dict(repo=str(repo),acceptance=str(a),objective='Keep app',checks=[['true']])))
  run=f.create(task);f.resume(run)
  page.get_by_role('heading',name=run+' · accepted').wait_for();page.get_by_text('Execution details and evidence').click()
  assert page.get_by_role('link',name='change.patch',exact=True).is_visible()
  with page.expect_navigation():page.get_by_role('link',name='change.patch',exact=True).click()
  assert page.url.endswith('artifact?name=change.patch')
  page.goto(base);page.get_by_role('heading',name=run+' · accepted').wait_for();page.screenshot(path=str(out/'desktop-light.png'))
  page.set_viewport_size({'width':375,'height':812});page.emulate_media(color_scheme='dark');page.get_by_text('Execution details and evidence').click();page.screenshot(path=str(out/'mobile-dark.png'))
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
  http.shutdown();http.server_close();page.get_by_text('Disconnected — showing last snapshot.',exact=False).wait_for(timeout=10000)
  assert page.get_by_role('heading',name=run+' · accepted').is_visible();page.screenshot(path=str(out/'disconnected.png'))
  http=server(state,port);threading.Thread(target=http.serve_forever,daemon=True).start();page.get_by_text('Connected · refreshed',exact=False).wait_for(timeout=10000)
  print('Rendered desktop light/mobile dark: empty and accepted state, artifact link, no horizontal overflow, disconnect retains snapshot, reconnect PASS')
  browser.close()
 http.shutdown();http.server_close()
 # Identical route and HTTP client; only existence of initialized storage differs.
 missing=server(root/'fresh-uninitialized',0);threading.Thread(target=missing.serve_forever,daemon=True).start()
 try:
  try:
   urllib.request.urlopen(f'http://127.0.0.1:{missing.server_port}/api/runs').read()
   print('Fresh-state probe unexpectedly returned data')
  except Exception as e: print('Fresh-state defect:',type(e).__name__,str(e))
 finally:missing.shutdown();missing.server_close()
