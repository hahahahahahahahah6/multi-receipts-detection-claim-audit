"""Read-only Markdown matching and module-local Python AST evidence analysis."""

import ast
import os
from pathlib import Path
import re

from .phrases import GENERIC_NAMES, MULTIRECEIPTSDETECTION, NOMULTIRECEIPTSDETECTION

POSITIVE_RULE = 'documented-multi-receipts-detection-claim-false'
NEGATIVE_RULE = 'documented-no-multi-receipts-detection-claim-false'


def normalize(text):
    return ' '.join(text.lower().replace("n't", ' not').replace('-', ' ').split())


def pattern(phrases):
    return re.compile(r'\b(?:' + '|'.join(re.escape(p) for p in sorted(phrases, key=lambda p: (-len(p), p))) + r')\b')


POSITIVE_PATTERN = pattern(MULTIRECEIPTSDETECTION)
NEGATIVE_PATTERN = pattern(NOMULTIRECEIPTSDETECTION)


def paragraphs(text):
    """Yield prose paragraphs and their starting line, respecting Markdown fences."""
    fence = None
    lines = []
    start = 1
    for number, line in enumerate(text.splitlines(), 1):
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= fence[1] and not marker[2].strip():
                fence = None
            continue
        if marker:
            if lines:
                yield start, '\n'.join(lines)
                lines = []
            fence = (marker[1][0], len(marker[1]))
        elif not line.strip():
            if lines:
                yield start, '\n'.join(lines)
                lines = []
        else:
            if not lines:
                start = number
            lines.append(line)
    if lines:
        yield start, '\n'.join(lines)


def document_claims(text, path):
    claims = []
    for line, paragraph in paragraphs(text):
        value = normalize(paragraph)
        denials = list(NEGATIVE_PATTERN.finditer(value))
        for match in denials:
            claims.append(dict(family='NOMULTIRECEIPTSDETECTION', phrase=match[0], path=path, line=line))
        value = NEGATIVE_PATTERN.sub(lambda m: ' ' * len(m[0]), value)
        for match in POSITIVE_PATTERN.finditer(value):
            claims.append(dict(family='MULTIRECEIPTSDETECTION', phrase=match[0], path=path, line=line))
    return claims


def target_names(node):
    return {part.id for part in ast.walk(node) if isinstance(part, ast.Name) and isinstance(part.ctx, ast.Store)}


def module_evidence(text, path, test=False):
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return []
    imports = {}
    roots = set()
    bound = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                roots.add(item.name.split('.')[0])
                imports[item.asname or item.name.split('.')[0]] = item.name if item.asname else item.name.split('.')[0]
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            if not node.level:
                roots.add(module.split('.')[0])
                for item in node.names:
                    imports[item.asname or item.name] = module + '.' + item.name
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                bound.update(target_names(target))
        elif isinstance(node, ast.AnnAssign):
            bound.update(target_names(node.target))
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars:
                    bound.update(target_names(item.optional_vars))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]

    def root_name(node):
        while isinstance(node, ast.Attribute):
            node = node.value
        return node.id if isinstance(node, ast.Name) else None

    def shadowed(node):
        name = root_name(node)
        return name in imports and name in bound

    def named(node, name):
        return ((isinstance(node, ast.Name) and node.id == name and name not in bound)
                or (isinstance(node, ast.Attribute) and node.attr == name and name not in bound and not shadowed(node)))

    def client(node):
        if isinstance(node, ast.Name):
            return node.id not in bound and imports.get(node.id) == 'mindee.Client' and 'Client' not in bound
        return (isinstance(node, ast.Attribute) and node.attr == 'Client' and 'Client' not in bound
                and isinstance(node.value, ast.Name) and node.value.id == 'mindee' and 'mindee' not in bound)

    has_client = 'mindee' in roots and any(client(call.func) for call in calls)
    evidence = []
    for call in calls:
        func = call.func
        route = None
        if isinstance(func, ast.Attribute):
            if func.attr in GENERIC_NAMES and func.attr not in bound and not shadowed(func):
                route = 'generic:' + func.attr
            elif (has_client and func.attr == 'parse' and 'parse' not in bound and not shadowed(func)
                  and any(named(arg, 'MultiReceiptsDetectorV1') for arg in list(call.args) + [kw.value for kw in call.keywords])):
                route = 'mindee:MultiReceiptsDetectorV1'
        elif isinstance(func, ast.Name) and func.id not in bound:
            resolved = imports.get(func.id, '').rsplit('.', 1)[-1]
            if resolved in GENERIC_NAMES and resolved not in bound:
                route = 'generic:' + resolved
        if route:
            evidence.append(dict(path=path, line=call.lineno, route=route, test=test))
    return sorted(evidence, key=lambda item: (item['line'], item['route']))


def audit(root, ignore=()):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise OSError('repository must be an existing, non-symlink directory: ' + str(root))
    prefixes = [tuple(Path(prefix).parts) for prefix in ignore if prefix and prefix != '.']
    ignore_all = '.' in ignore

    def ignored(parts):
        return ignore_all or any(parts[:len(prefix)] == prefix for prefix in prefixes)

    claims, evidence = [], []
    source_files = 0

    def walk_error(error):
        raise error

    for directory, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        relative = Path(directory).relative_to(root)
        dirs[:] = sorted(name for name in dirs if not (Path(directory) / name).is_symlink()
                         and not ignored((relative / name).parts))
        for name in sorted(files):
            file = Path(directory) / name
            rel = file.relative_to(root)
            if file.is_symlink() or ignored(rel.parts):
                continue
            doc = rel.as_posix() == 'README.md' or (file.suffix == '.md' and 'docs' in rel.parts[:-1])
            source = file.suffix == '.py' and not {'fixtures', 'docs', 'examples'}.intersection(rel.parts[:-1])
            if not doc and not source:
                continue
            text = file.read_text(encoding='utf-8')
            if doc:
                claims.extend(document_claims(text, rel.as_posix()))
            if source:
                source_files += 1
                test = 'tests' in rel.parts[:-1] or (name.startswith('test_') or name.endswith('_test.py'))
                evidence.extend(module_evidence(text, rel.as_posix(), test))
    production = [item for item in evidence if not item['test']]
    tests = [item for item in evidence if item['test']]
    findings = []
    positive = [item for item in claims if item['family'] == 'MULTIRECEIPTSDETECTION']
    negative = [item for item in claims if item['family'] == 'NOMULTIRECEIPTSDETECTION']
    if positive and not production:
        findings.append(dict(rule=POSITIVE_RULE, severity='MEDIUM' if tests else 'HIGH',
                             message='Documented promise lacks production evidence.', claims=positive))
    if negative and production:
        findings.append(dict(rule=NEGATIVE_RULE, severity='HIGH',
                             message='Documented denial contradicts production evidence.', claims=negative))
    return dict(verdict='FAIL' if findings else 'PASS', findings=findings, claims=claims,
                evidence=evidence, source_files=source_files)
