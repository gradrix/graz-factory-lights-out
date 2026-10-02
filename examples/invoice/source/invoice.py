"""Summarize invoice CSV amounts by customer."""
import csv
import json
import sys


def summarize(stream):
    totals = {}
    for row in csv.DictReader(stream):
        customer = row['customer']
        totals[customer] = totals.get(customer, 0.0) + float(row['amount'])
    return {key: str(round(value, 2)) for key, value in totals.items()}


if __name__ == '__main__':
    with open(sys.argv[1], newline='') as stream:
        print(json.dumps(summarize(stream), sort_keys=True))
