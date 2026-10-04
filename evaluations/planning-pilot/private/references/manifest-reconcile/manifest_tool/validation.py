import re

def entries(value):
    if not isinstance(value,list) or len(value)>100: raise ValueError('entries')
    result={}
    for item in value:
        if not isinstance(item,dict) or set(item)!={'path','size','sha256'}: raise ValueError('entry')
        path=item['path'];size=item['size'];digest=item['sha256']
        if not isinstance(path,str) or not 1<=len(path)<=120 or any(not re.fullmatch(r'[A-Za-z0-9_.-]+',p) or p in ('.','..') for p in path.split('/')): raise ValueError('path')
        if path in result or type(size)is not int or not 0<=size<=1000000 or not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest): raise ValueError('entry')
        result[path]={'path':path,'size':size,'sha256':digest}
    return result
