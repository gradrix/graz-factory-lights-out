def legacy(p):return [c['id'] for c in p['changes']]

def feature(p):
 last={};[last.setdefault(c['id'],i) for i,c in enumerate(p['changes'])];sections=[]
 for cat in ['added','fixed','removed']:
  rows=[c for i,c in enumerate(p['changes']) if last[c['id']]==i and not c['internal'] and c['category']==cat]
  if rows:sections.append('## '+cat.title()+'\n'+'\n'.join('- '+' '.join(c['title'].split()) for c in rows))
 return '\n\n'.join(sections)+'\n' if sections else ''
