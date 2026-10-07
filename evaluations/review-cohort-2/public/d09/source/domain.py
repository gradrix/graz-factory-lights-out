def legacy(p):return [x['id'] for x in p['invoices']]

def feature(p):
 import csv,io
 stream=io.StringIO(newline='');w=csv.writer(stream,lineterminator='\r\n');w.writerow(['id','customer','total'])
 for inv in p['invoices']:
  cents=sum(x['quantity']*x['unit_cents'] for x in inv['items']);w.writerow([inv['id'],inv['customer'],str(cents//100)+'.'+str(cents%100).zfill(2)])
 return stream.getvalue()
