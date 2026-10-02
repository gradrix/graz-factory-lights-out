import argparse
import json
from store import initialize, put, available


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('database')
    parser.add_argument('action', choices=['put', 'get'])
    parser.add_argument('sku')
    parser.add_argument('quantity', nargs='?', type=int)
    args = parser.parse_args()
    initialize(args.database)
    if args.action == 'put':
        put(args.database, args.sku, args.quantity)
    print(json.dumps({'sku': args.sku, 'quantity': available(args.database, args.sku)}))


if __name__ == '__main__':
    main()
