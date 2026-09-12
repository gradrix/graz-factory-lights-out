import io
import tracemalloc
from tabular import summarize

assert summarize(io.StringIO('label,quantity\n'))==[]
raw='label,quantity\r\n" ž,blue ",+03\r\na,-1\r\na,1\r\n'
assert summarize(io.StringIO(raw,newline=''))==[dict(label='a',quantity=0),dict(label='ž,blue',quantity=3)]
cases=[('',1),('quantity,label\n',1),('label,quantity\n\n',2),('label,quantity\nx,1,extra\n',2),('label,quantity\nx,"1',2),('label,quantity\n"x"junk,1\n',2)]
for label in ['\nx','x\n','x\r',' ','x'*121]:
    cases.append(('label,quantity\n"'+label+'",1\n',2))
for qty in ['1.0','١','+','1e2',' 1','1 ','1000000001','12345678901','1\n']:
    cases.append(('label,quantity\nx,"'+qty+'"\n',2))
for raw,row in cases:
    try: summarize(io.StringIO(raw,newline=''))
    except ValueError as exc: assert f'row {row}' in str(exc), (raw,str(exc))
    else: raise AssertionError(('invalid CSV accepted',repr(raw)))
for options in ({'max_rows':1},{'max_labels':1},{'max_rows':True},{'max_labels':0}):
    try: summarize(io.StringIO('label,quantity\na,1\nb,2\n'),**options)
    except ValueError: pass
    else: raise AssertionError(('limit ignored',options))
try: summarize(io.TextIOWrapper(io.BytesIO(b'\xff'),encoding='utf-8'))
except ValueError as exc: assert 'row ' in str(exc)
else: raise AssertionError('bad UTF-8 accepted')
def many():
    yield 'label,quantity\n'
    for _ in range(200000): yield 'a,1\n'
tracemalloc.start()
assert summarize(many())==[dict(label='a',quantity=200000)]
_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
assert peak<2*1024*1024, ('all rows buffered',peak)
print('tabular-ok')
