import argparse
import json
import sys
from store import initialize, put, available, reserve


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('database')
    parser.add_argument('action', choices=['put', 'get', 'reserve'])
    parser.add_argument('sku')
    parser.add_argument('quantity', nargs='?', type=int)
    args = parser.parse_args()
    initialize(args.database)
    if args.action == 'put':
        put(args.database, args.sku, args.quantity)
        print(json.dumps({'sku': args.sku, 'quantity': available(args.database, args.sku)}))
    elif args.action == 'get':
        print(json.dumps({'sku': args.sku, 'quantity': available(args.database, args.sku)}))
    else:  # reserve
        if not isinstance(args.quantity, int) or args.quantity <= 0:
            print('reserve requires a positive integer quantity', file=sys.stderr)
            sys.exit(2)
        reserved = reserve(args.database, args.sku, args.quantity)
        remaining = available(args.database, args.sku)
        print(json.dumps({'sku': args.sku, 'reserved': reserved, 'quantity': remaining}))


if __name__ == '__main__':
    main()
