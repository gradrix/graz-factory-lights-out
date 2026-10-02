from fastapi import FastAPI
from .schemas import SumRequest
from .domain import total
app=FastAPI()
@app.get('/health')
def health():return {'status':'ok'}
@app.post('/sum')
def sum_values(body:SumRequest):return {'total':total(body.values)}
