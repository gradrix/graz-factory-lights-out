from fastapi import APIRouter,Body
from fastapi.responses import JSONResponse
from .domain import preview
from .errors import Conflict
router=APIRouter()
@router.post('/config/preview')
def config_preview(payload=Body(...)):
    if not isinstance(payload,dict) or set(payload)!={'base','operations'}:return JSONResponse(status_code=422,content={'error':'invalid input'})
    try:return preview(payload['base'],payload['operations'])
    except Conflict as error:return JSONResponse(status_code=409,content={'error':{'index':error.index,'code':error.code}})
    except ValueError:return JSONResponse(status_code=422,content={'error':'invalid input'})
