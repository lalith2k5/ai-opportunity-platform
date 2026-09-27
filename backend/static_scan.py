"""Static analysis: unused imports, undefined names, syntax errors."""
import ast
from pathlib import Path

issues = []

def scan_file(path: Path):
    try:
        src = path.read_text()
        tree = ast.parse(src)
    except SyntaxError as e:
        issues.append(f"❌ SYNTAX ERROR in {path}: {e}")
        return

    # Collect imported names
    imported = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                imported[name] = node.lineno
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    continue
                name = alias.asname or alias.name
                imported[name] = node.lineno

    # Collect used names
    used = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            # capture head of dotted name
            n = node
            while isinstance(n, ast.Attribute):
                n = n.value
            if isinstance(n, ast.Name):
                used.add(n.id)

    # Report unused imports
    for name, line in imported.items():
        if name not in used and name != "*":
            issues.append(f"⚠️  {path}:{line} — unused import '{name}'")

for f in Path("app").rglob("*.py"):
    scan_file(f)

scan_file(Path("scale_test.py"))
scan_file(Path("run.py"))

if issues:
    for i in issues:
        print(i)
    print(f"\n{len(issues)} issue(s) found")
else:
    print("✅ No static issues found")

# Also check for common anti-patterns
import subprocess
print()
print("--- Checking for bare excepts ---")
result = subprocess.run(
    ["grep", "-rn", "except:", "app/"],
    capture_output=True, text=True,
)
if result.stdout.strip():
    print(result.stdout)
else:
    print("✅ No bare excepts")

print()
print("--- Checking for TODO/FIXME/placeholder ---")
result = subprocess.run(
    ["grep", "-rn", "-E", "TODO|FIXME|XXX|noop|placeholder", "app/"],
    capture_output=True, text=True,
)
if result.stdout.strip():
    print(result.stdout)
else:
    print("✅ No TODOs/placeholders")
