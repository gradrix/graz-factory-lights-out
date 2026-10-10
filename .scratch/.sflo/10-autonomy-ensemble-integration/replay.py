"""Replay stored qualified-trial role answers through maintained gflo.ensemble judging; no model calls."""
import json, sys
from pathlib import Path
from gflo import ensemble as e
from gflo.review import validate
results = {}
for trial, cohort in zip(sys.argv[1::2], sys.argv[2::2]):
    manifest = json.loads((Path(cohort) / 'manifest.json').read_text())
    for case in manifest['cases']:
        root = Path(trial) / case['id']
        objective = (Path(cohort) / case['objective']).read_text()
        source = Path(cohort) / case['source']
        files = {str(p.relative_to(source)): p.read_text() for p in sorted(source.rglob('*')) if p.is_file()}
        catalog = json.loads((root / 'catalog.json').read_text())
        found = e.statements(objective); planned = e.units(found)
        child = json.loads((root / 'judging' / 'child-result.json').read_text())
        units = child['units'] if 'units' in child else child['child']['units']
        mismatches = []; replayed = []
        for stored, unit in zip(units, planned):
            assert stored['ids'] == unit['ids']
            roles = stored['roles']; chunks = e.audit_chunks(catalog)
            parts = [e.validate_audit(roles[f'audit-{i}']['value'], catalog, ids) for i, ids in enumerate(chunks, 1)]
            audit = e.merge_audits(parts)
            prosecutor = e.validate_unit(roles['prosecutor']['value'], found, files, catalog, unit['ids'])
            disputes = e.contested(audit, prosecutor, files, catalog)
            if not disputes and prosecutor['decision'] == 'pass':
                decision, statement, findings = 'pass', None, []
                if any(k.startswith('judge') for k in roles): mismatches.append((unit['ids'], 'judge ran on clean unit'))
            else:
                verdicts = [e.validate_unit(roles[f'judge-{f}']['value'], found, files, catalog, unit['ids']) for f in e.PANEL]
                decision, statement, findings = e.panel_decision(verdicts, unit['ids'])
            if decision != stored['decision'] or statement != stored.get('panel_statement'):
                mismatches.append((unit['ids'], decision, stored['decision']))
            replayed.append({'status': 'accepted', 'decision': decision, 'panel_statement': statement, 'findings': findings})
        case_decision = e.aggregate(replayed, len(planned))
        review = e.to_review(replayed, found, files, catalog); validate(review, files)
        results[f"{Path(trial).parent.name}/{case['id']}"] = {'stored': child.get('decision') or child['child']['decision'],
            'replayed': case_decision, 'review': review['decision'], 'findings': len(review['findings']), 'mismatches': mismatches}
bad = {k: v for k, v in results.items() if v['mismatches'] or v['stored'] != v['replayed'] or v['review'] != v['replayed']}
print(json.dumps({'cases': len(results), 'agree': len(results) - len(bad), 'disagreements': bad}, indent=1))
print(json.dumps({k: [v['replayed'], v['findings']] for k, v in results.items()}))
