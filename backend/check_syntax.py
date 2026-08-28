from pathlib import Path
import py_compile

root = Path(__file__).parent / "app"
for path in sorted(root.rglob("*.py")):
    py_compile.compile(str(path), doraise=True)
    print(f"OK {path}")
