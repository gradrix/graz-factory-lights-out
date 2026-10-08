def field_names(payload):
    return sorted(payload['fields'])

import re

KEY = re.compile(r'[A-Za-z_][A-Za-z0-9_]*\Z')
def encode(payload):
    fields=payload['fields'];out=[]
    table={'\\':'\\\\','\t':'\\t','\n':'\\n','\r':'\\r'}
    for key in sorted(fields):
        if not KEY.fullmatch(key):raise ValueError('key')
        out.append(key+'='+''.join(table.get(c,c) for c in fields[key]))
    return '\t'.join(out)
def decode(payload):
    line=payload['line'];out={};table={'\\':'\\','t':'\t','n':'\n','r':'\r'}
    if line=='':return out
    for field in line.split('\t'):
        if '=' not in field:raise ValueError('field')
        key,value=field.split('=',1)
        if not KEY.fullmatch(key) or key in out:raise ValueError('key')
        chars=[];i=0
        while i<len(value):
            c=value[i];i+=1
            if c=='\\':
                if i==len(value) or value[i] not in table:raise ValueError('escape')
                c=table[value[i]];i+=1
            chars.append(c)
        out[key]=''.join(chars)
    return out
