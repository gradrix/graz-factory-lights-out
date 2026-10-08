import json,sys
from api import dispatch

def main():
    try:
        result=dispatch(json.load(sys.stdin))
    except (ValueError,KeyError) as error:
        sys.exit(str(error))
    print(json.dumps(result,ensure_ascii=False))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
