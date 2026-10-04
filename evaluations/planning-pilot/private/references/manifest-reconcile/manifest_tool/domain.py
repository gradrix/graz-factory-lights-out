from .validation import entries

def compare(before,after):
    left,right=entries(before),entries(after)
    common=left.keys() & right.keys()
    unchanged=sorted(p for p in common if (left[p]['size'],left[p]['sha256'])==(right[p]['size'],right[p]['sha256']))
    modified=[{'path':p,'before_size':left[p]['size'],'after_size':right[p]['size']} for p in sorted(common) if p not in unchanged]
    removed=set(left)-set(right);added=set(right)-set(left);renamed=[]
    signatures={(left[p]['size'],left[p]['sha256'])for p in removed}
    for sig in signatures:
        old=[p for p in removed if (left[p]['size'],left[p]['sha256'])==sig]
        new=[p for p in added if (right[p]['size'],right[p]['sha256'])==sig]
        if len(old)==len(new)==1:renamed.append({'from':old[0],'to':new[0]})
    for item in renamed:removed.remove(item['from']);added.remove(item['to'])
    return {'added':sorted(added),'removed':sorted(removed),'modified':modified,'renamed':sorted(renamed,key=lambda x:x['from']),'unchanged':unchanged}
