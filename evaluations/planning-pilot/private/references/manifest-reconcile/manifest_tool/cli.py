import json,sys
from .api import run

def main():
    try:result=run(json.load(sys.stdin))
    except (ValueError,TypeError):print(json.dumps({'error':'invalid input'}));return 2
    print(json.dumps(result,sort_keys=True));return 0
