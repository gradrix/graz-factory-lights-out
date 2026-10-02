#!/usr/bin/env python3
"""Copy the three example tasks into independent, committed local repositories."""
import argparse
from pathlib import Path
import shutil
import subprocess


def prepare(destination):
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError('Choose a new destination; existing pilot runs are never overwritten')
    destination.mkdir(parents=True)
    source = Path(__file__).resolve().parent
    for name in ('invoice', 'inventory', 'log-summary'):
        target = destination / name
        shutil.copytree(source / name, target)
        repo = target / 'source'
        for args in (['init', '-q'], ['add', '.'], ['-c', 'user.name=GFLO fixture', '-c', 'user.email=fixture@local', 'commit', '-qm', 'Initial example input']):
            subprocess.run(['git', '-C', str(repo), *args], check=True)
        print(target / 'task.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', nargs='?', default='.gflo/examples')
    prepare(parser.parse_args().destination)
