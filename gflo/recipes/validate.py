"""Parse bounded copied manifests; never import the project or resolve packages."""
import json
from pathlib import Path
import sys
import tomllib

profile = sys.argv[1]
root = Path('/inputs')
if profile == 'python-api':
    value = tomllib.loads((root / 'pyproject.toml').read_text())
    build = value.get('build-system', {})
    project = value.get('project', {})
    if build != {'requires': ['setuptools==78.1.0'], 'build-backend': 'setuptools.build_meta'}:
        raise ValueError('Supported build system: setuptools==78.1.0 with setuptools.build_meta only')
    if sorted(project.get('dependencies', [])) != ['fastapi==0.115.12', 'uvicorn==0.34.2']:
        raise ValueError('Supported dependencies: fastapi==0.115.12 and uvicorn==0.34.2 only')
    if project.get('optional-dependencies') or project.get('dynamic') or project.get('requires-python') != '>=3.12,<3.13':
        raise ValueError('Use fixed dependencies and requires-python >=3.12,<3.13')
elif profile == 'node-ts':
    manifest = json.loads((root / 'package.json').read_text())
    lock = json.loads((root / 'package-lock.json').read_text())
    approved = json.loads(Path('/approved/package-lock.json').read_text())
    dependencies = {'typescript': '5.8.3', '@types/node': '22.15.3'}
    if (manifest.get('devDependencies') != dependencies or manifest.get('dependencies') or
            manifest.get('optionalDependencies') or manifest.get('peerDependencies') or
            manifest.get('workspaces') or manifest.get('overrides') or manifest.get('scripts') or
            manifest.get('type') != 'commonjs' or manifest.get('engines') != {'node': '>=22 <23'}):
        raise ValueError('Supported Node profile: CommonJS Node22, TypeScript5.8.3 and @types/node22.15.3 only; no scripts/workspaces/overrides')
    packages = lock.get('packages', {})
    if lock.get('lockfileVersion') != 3 or {k:v for k,v in packages.items() if k} != {k:v for k,v in approved['packages'].items() if k}:
        raise ValueError('Project package-lock.json differs from the approved complete dependency lock')
    expected = {k: manifest[k] for k in ('name', 'version', 'devDependencies', 'engines')}
    if packages.get('') != expected or lock.get('name') != manifest['name'] or lock.get('version') != manifest['version']:
        raise ValueError('Project manifest and lock root disagree')
else:
    raise ValueError('Unsupported manifest validation profile')
print(json.dumps({'passed': True}))
