# Supervised local browser checks — accepted

2026-10-04. Accepted source **596ecb6**, manifest **ee60bbe4012e03acbcd5a9cd403a63f62290dd253c97a7f7979ead062ee53ea4**. Contract SHA256 **ab3ba1d7aa4d11237de3914f2a1ed40d3dcb47a680ee181465ef8fba6b875f13**; unit/run links and identity verified at closure.

## Evidence

- [Independent rig QA](qa-rig-browser.md): five application journeys and five discriminating mutants pass expected outcomes in27.649s; complete screenshots and all-context traces independently inspected. Fifteen supplemental controls, actual startup cancellation and two owner-death phases pass. Four additional target seam tests are explicitly controlled injections. Private redirect/WebSocket prevention requires zero side-server hits. Renderer isolation, exact mounts/resources/noGPU and7.0–13.1MB sampled shared-memory use are observed on the actual rig.
- [Final seed security review](security-browser-v5.md):24 focused cases pass; carries unchanged [v4 recovery review](security-browser-v4.md) and [v3 boundary recheck](security-browser-recheck.md) only after exact delta verification. No actual daemon outage or arbitrary hostile-site certification is claimed.
- Builder full gate on v3:144tests/86% branch-aware coverage. Subsequent narrow fixes passed26 affected tests for private guardian permissions and31 affected tests for seed reading. These are separate results, not a newly measured full-suite coverage result for v5. [V5 repair](builder-repair-v5.md).
- [Installed source receipt](rig-runtime-promotion.json): all29 tracked source/assets verified at MONSTER-GAMING-PC ~/gflo-runtime; model doctor reports ready,98304context. Config preserved. The earlier Python-only installation omitted seven environment recipe assets; this complete-tree installation restores them. Prior source copy removed after readback. [Prepared browser support](rig-runtime-support.json) is available in the normal runtime store and inspect readback matches.

## Preserved failures

Original candidate had cancellation, redirect/WebSocket, daemon-log and ambiguous-create defects; independent review found a later umask mismatch. First v4 rig trial passed create/reload then rejected an unchanged seed because reading changed atime; raw results remain in rig-v4-failed. V5 repairs that cause while retaining mutation/replacement/link refusal. The v5 outer harness completed all product controls then hit a Python NameError before lifecycle dispatch; its original log is retained, dispatch fixed, and only unfinished lifecycle checks ran separately. No failed trial was rewritten or silently counted as passing.

## Qualified scope

One frozen reviewed Playwright journey against a disposable Node built-ins app, with bounded evidence and recovery. All redirects and WebSockets are unsupported in this first profile. Trusted checks use approved targets; page content has no tool authority. This qualifies a browser verifier, not local-model web-app generation, public browsing/search, full Stage4, autonomous planning/integration or power-loss durability.

Full private rig evidence: /home/gradrix/gflo-browser-596ecb6/.gflo/rig-qualification-v5. Compact independently checked evidence: qa-rig-browser/. Next discovery concerns document extraction/citation reliability; broader autonomous delivery remains the destination.

Installation smoke: the normal runtime CLI ran the prepared create/reload approval and passed; offline inspect matched result189b2d56b22c1f85055688950488c92eeaba15eb63b2a71ac96c4e4294eeb094. [Receipt](rig-installed-smoke.json). The example approval is ~/gflo-runtime/.gflo/browser-example.json. This checks deployment packaging and paths, not an additional unseen task.
