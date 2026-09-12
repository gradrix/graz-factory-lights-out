import argparse, json, pathlib, sys
import core

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)
    try:
        result = core.run(pathlib.Path(args.path).read_text(encoding='utf-8'))
    except (ValueError, OSError) as exc:
        print('error:', exc, file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 0

if __name__ == '__main__':
    sys.exit(main())
