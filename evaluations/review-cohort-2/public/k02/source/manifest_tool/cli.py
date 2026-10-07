import json,sys
from .api import run

def main():
    try:result=run(json.load(sys.stdin))
    except (ValueError,TypeError,KeyError,AttributeError,RecursionError):print(json.dumps({'error':'invalid input'},separators=(',',':')));return 2
    print(json.dumps(result,sort_keys=True,separators=(',',':')));return 0
