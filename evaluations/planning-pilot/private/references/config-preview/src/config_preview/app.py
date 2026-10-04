from fastapi import FastAPI,Body
from fastapi.responses import JSONResponse
from .routes import router
app=FastAPI();app.include_router(router)
@app.get('/health')
def health():return {'status':'ok'}
@app.post('/sum')
def total(payload=Body(...)):
    if not isinstance(payload,dict) or set(payload)!={'values'} or not isinstance(payload['values'],list) or any(type(x)is not int for x in payload['values']):return JSONResponse(status_code=422,content={'error':'invalid input'})
    return {'total':sum(payload['values'])}
