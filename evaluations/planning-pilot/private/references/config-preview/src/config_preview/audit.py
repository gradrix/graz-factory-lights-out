import copy

def event(index,op,path,before_present,before_value,after_present,after_value):
    return {'index':index,'op':op,'path':list(path),'before':{'present':before_present,'value':copy.deepcopy(before_value) if before_present else None},'after':{'present':after_present,'value':copy.deepcopy(after_value) if after_present else None}}
