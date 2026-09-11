"""Execute all notebooks in this directory and save outputs in-place."""
import subprocess
import sys
from pathlib import Path

notebooks = sorted(Path(__file__).parent.glob("*.ipynb"))

if not notebooks:
    print("No .ipynb files found.")
    sys.exit(0)

for nb in notebooks:
    print(f"Executing {nb.name}...")
    result = subprocess.run(
        [sys.executable, "-m", "jupyter", "nbconvert",
         "--to", "notebook", "--execute", "--inplace", str(nb)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"FAILED: {nb.name}\n{result.stderr}")
        sys.exit(result.returncode)
    print(f"  done.")

print(f"\nExecuted {len(notebooks)} notebook(s).")
