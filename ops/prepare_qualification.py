#!/usr/bin/env python3
"""Materialize published, hash-checked fixtures into disposable Git repositories."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def prepare(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination.exists():
        raise ValueError('Choose a new destination; existing qualification data is never overwritten')
    manifest = json.loads((source / 'manifest.json').read_text())
    for name, expected in manifest['sha256'].items():
        path = source / name
        if not path.resolve().is_relative_to(source) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Fixture manifest mismatch: ' + name)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))
    repos = sorted((destination / 'coding').glob('*/source')) + [destination / 'ambiguous/source']
    for repo in repos:
        for args in (['init','-q'], ['add','.'], ['-c','user.name=GFLO qualification','-c','user.email=qualification@local','commit','-qm','Frozen qualification input']):
            subprocess.run(['git','-C',str(repo),*args], check=True)
    print(destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination')
    parser.add_argument('--source', default='evaluations/local-review')
    args = parser.parse_args()
    prepare(args.source, args.destination)
