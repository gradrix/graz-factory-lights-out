"""Repository map for the worker's map tool. Standard library only; runs inside the read-only sandbox.

usage: python repo_map.py ROOT [QUERY]

Without QUERY: one line per Python module with its top-level definitions. QUERY ending in .py: that module's
definitions with signatures and line numbers, and the modules importing it. Any other QUERY: definitions of that
name and the lines using it. Output is bounded; nothing is executed or imported from the repository.
"""
import ast
import os
import sys

LIMIT = 16000
MAX_FILE = 1_000_000
SKIP = {'__pycache__', 'node_modules', 'venv', 'build', 'dist'}
DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def python_files(root):
    for directory, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP and not d.startswith('.'))
        for name in sorted(files):
            path = os.path.join(directory, name)
            if name.endswith('.py') and not os.path.islink(path) and os.path.getsize(path) <= MAX_FILE:
                yield os.path.relpath(path, root)


def parse(root, rel):
    try:
        with open(os.path.join(root, rel), encoding='utf-8', errors='replace') as stream:
            source = stream.read()
        return ast.parse(source), source.splitlines()
    except (OSError, SyntaxError, ValueError, RecursionError, MemoryError):
        return None, []


def module_name(rel):
    parts = rel[:-3].split(os.sep)
    if parts[0] == 'src':
        parts = parts[1:]
    if parts[-1] == '__init__':
        parts = parts[:-1]
    return '.'.join(parts)


def imported(rel, node):
    """Absolute module names an import statement in module REL names, including imported submodules."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []
    base = node.module or ''
    if node.level:
        package = module_name(rel).split('.')
        if not rel.endswith('__init__.py'):
            package = package[:-1]
        package = package[:len(package) - (node.level - 1)] if node.level > 1 else package
        base = '.'.join(package + ([node.module] if node.module else []))
    return [base] + [f'{base}.{alias.name}' if base else alias.name for alias in node.names]


def source(node):
    try:
        return ast.unparse(node)
    except (RecursionError, ValueError):
        return '...'


LINE = 300  # one pathological definition must not crowd out the rest of the answer


def signature(node):
    if isinstance(node, ast.ClassDef):
        bases = ', '.join(source(base) for base in node.bases)
        return f'class {node.name}({bases})' if bases else f'class {node.name}'
    prefix = 'async def' if isinstance(node, ast.AsyncFunctionDef) else 'def'
    returns = f' -> {source(node.returns)}' if node.returns else ''
    text = f'{prefix} {node.name}({source(node.args)}){returns}'
    return text if len(text) <= LINE else text[:LINE] + ' ...'


def summary(node):
    doc = ast.get_docstring(node) if isinstance(node, (ast.Module, *DEFINITIONS)) else None
    return doc.strip().splitlines()[0][:100] if doc and doc.strip() else ''


def is_test(rel):
    return rel.split(os.sep)[0] in ('tests', 'test') or os.path.basename(rel).startswith('test_')


def overview(root, names_shown=6, docs=True):
    packaged, folded, tests = [], {}, {}
    for rel in python_files(root):
        directory = os.path.dirname(rel)
        if is_test(rel):
            tests[directory or '.'] = tests.get(directory or '.', 0) + 1
        elif directory and not os.path.exists(os.path.join(root, directory, '__init__.py')):
            folded.setdefault(directory, []).append(os.path.basename(rel))
        else:
            packaged.append(rel)
    lines = []
    for rel in packaged:
        tree, _ = parse(root, rel)
        if tree is None:
            lines.append(f'{rel}: (does not parse)')
            continue
        names = [node.name for node in tree.body if isinstance(node, DEFINITIONS)]
        public = [name for name in names if not name.startswith('_')] or names
        hidden = len(names) - len(public[:names_shown])
        shown = ' '.join(filter(None, [', '.join(public[:names_shown]), f'+{hidden}' if hidden else '']))
        doc = summary(tree)[:60] if docs else ''
        lines.append(rel + (f' — {doc}' if doc else '') + (f': {shown}' if names else ''))
    lines += [f'{directory}/: {len(names)} modules (not a package): ' + ', '.join(names[:6]) + (' …' if len(names) > 6 else '')
              for directory, names in sorted(folded.items())]
    lines += [f'{directory}/: {count} test modules' for directory, count in sorted(tests.items())]
    lines.append('Query a module path for signatures and importers, or a name for definitions and usages.')
    return lines


def module_detail(root, rel):
    if not os.path.isfile(os.path.join(root, rel)) or os.path.islink(os.path.join(root, rel)):
        return [f'{rel}: no such module; map() lists the modules']
    tree, _ = parse(root, rel)
    if tree is None:
        return [f'{rel}: not found or does not parse']
    lines = [f'{rel}' + (f' — {summary(tree)}' if summary(tree) else '')]
    for node in tree.body:
        if isinstance(node, DEFINITIONS):
            doc = summary(node)
            lines.append(f'  {node.lineno}: {signature(node)}' + (f'  # {doc}' if doc else ''))
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, DEFINITIONS):
                        lines.append(f'    {child.lineno}: {signature(child)}')
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = [target.id for target in targets if isinstance(target, ast.Name)]
            if names:
                lines.append(f'  {node.lineno}: {", ".join(names)} = ...')
    target = module_name(rel)
    importers = []
    for other in python_files(root):
        other_tree, _ = parse(root, other)
        if other == rel or other_tree is None:
            continue
        if any(target in imported(other, node) for node in ast.walk(other_tree)):
            importers.append(other)
    lines.append('imported by: ' + (', '.join(importers) if importers else 'no module'))
    return lines


def name_detail(root, query):
    definitions, usages = [], []
    for rel in python_files(root):
        tree, source = parse(root, rel)
        if tree is None:
            continue
        seen = set()
        for node in ast.walk(tree):
            if isinstance(node, DEFINITIONS) and node.name == query:
                definitions.append(f'{rel}:{node.lineno}: {signature(node)}' + (f'  # {summary(node)}' if summary(node) else ''))
                continue
            used = ((isinstance(node, ast.Name) and node.id == query)
                    or (isinstance(node, ast.Attribute) and node.attr == query)
                    or (isinstance(node, ast.alias) and query in (node.name.split('.')[-1], node.asname)))
            line = getattr(node, 'lineno', None)
            if used and line and line not in seen:
                seen.add(line)
                text = source[line - 1].strip() if line <= len(source) else ''
                usages.append(f'{rel}:{line}: {text[:140]}')
    if not definitions and not usages:
        return [f'No definition or usage of {query!r}. The map matches exact Python names; try run with grep.']
    return (['definitions:'] + (definitions or ['  none in the repository (imported from a dependency?)'])
            + [f'usages ({len(usages)}):'] + usages)


def main(argv):
    root = argv[1]
    query = argv[2].strip() if len(argv) > 2 else ''
    if not query:
        lines = overview(root)
        for names_shown, docs in ((6, False), (3, False), (0, False)):  # list every module before detail
            if len('\n'.join(lines).encode()) <= LIMIT:
                break
            lines = overview(root, names_shown, docs)
    elif query.endswith('.py'):
        lines = module_detail(root, os.path.normpath(query.removeprefix('/workspace/')))
    else:
        lines = name_detail(root, query)
    text = '\n'.join(lines)
    notice = '\n... map output truncated; query a narrower module path or name.'
    if len(text.encode()) > LIMIT:
        head = text.encode()[:LIMIT - len(notice.encode())].decode(errors='ignore')
        text = head.rsplit('\n', 1)[0] + notice
    print(text)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
