def sources(payload):
    return sorted({event['source'] for event in payload['events']})

from copy import deepcopy

def ingest(payload):
    start=payload['watermarks'];marks=deepcopy(start);groups={}
    for event in payload['events']:
        source=event['source'];seq=event['seq'];marks.setdefault(source,0)
        group=groups.setdefault(source,{})
        if seq in group and group[seq]['data']!=event['data']:raise ValueError('conflicting event')
        group[seq]=deepcopy(event)
    released=[];pending=[]
    for source in sorted(groups):
        group={seq:event for seq,event in groups[source].items() if seq>start.get(source,0)}
        while marks[source]+1 in group:
            marks[source]+=1;released.append(group.pop(marks[source]))
        pending.extend(group[seq] for seq in sorted(group))
    return {'watermarks':marks,'released':released,'pending':pending}
