"""Перевіряє, що зміни після BASE — лише коментарі: код, шаблони, JS і CSS без коментарів лишились ідентичні.

Python: AST кожного файлу без docstring-ів має збігатися з BASE. Шаблони: без {# ... #}. JS: без рядків-коментарів //.
CSS: без /* ... */. Використання: `python scripts/check_comment_only.py [BASE]` (типово HEAD, порівнює робоче дерево).
Код виходу 1, якщо змінилося щось, крім коментарів.
"""
import ast
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def strip_docstrings(tree):
    """AST без docstring-ів модуля, класів і функцій (порожнє тіло отримує pass, як без docstring-а)."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                node.body = body[1:] or [ast.Pass()]
    return ast.dump(tree, annotate_fields=True, include_attributes=False)


def normalise(path, text):
    """Текст файлу без коментарів того типу, який дозволено додавати."""
    if path.endswith(".py"):
        return strip_docstrings(ast.parse(text))
    if path.endswith(".html"):
        return re.sub(r"\{#.*?#\}", "", text)
    if path.endswith(".js"):
        return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("//"))
    if path.endswith(".css"):
        return re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return None


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def main(base="HEAD"):
    changed = [line.split("\t") for line in git("diff", "--name-status", base).splitlines()]
    problems, checked = [], 0
    for status, *paths in changed:
        path = paths[-1]
        if path == "scripts/check_comment_only.py" or path.endswith(".md"):
            continue
        if status != "M":
            problems.append(f"{status} {path}: added, deleted or renamed")
            continue
        old, new = git("show", f"{base}:{path}"), (ROOT / path).read_text(encoding="utf-8")
        before, after = normalise(path, old), normalise(path, new)
        if before is None:
            problems.append(f"{path}: not a .py/.html/.js/.css file")
        elif before != after:
            problems.append(f"{path}: more than comments changed")
        checked += 1
    for problem in problems:
        print(problem)
    print(f"{checked} files checked against {base}: " + ("only comments changed." if not problems else "PROBLEMS above."))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:2]))
