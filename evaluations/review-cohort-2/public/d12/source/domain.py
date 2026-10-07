def legacy(p):return [a['id'] for a in p['artifacts']]

def feature(p):
 eligible=[a for a in p['artifacts'] if a['platform']==p['platform'] and not a['yanked'] and int(a['version'].split('.')[0])==p['major']]
 p['artifacts'].sort(key=lambda a:a['id'])
 if not eligible:return None
 a=min(eligible,key=lambda a:(tuple(-int(x) for x in a['version'].split('.')),a['id']))
 return {'id':a['id'],'version':a['version']}
