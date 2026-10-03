"""Runs ONLY the sequential-vs-parallel identity test of the notebook (Section 8.1), without executing
the whole notebook: it executes the cells tagged `core` (parameters, data, indices, functions, task
definitions) and then the cell tagged `identity`, in one shared namespace, from the notebook file itself.

Usage (from the repository root):  python scripts/identity_test.py
Exit code 0 = the parallel run reproduces the sequential run bit for bit.
"""
import ast
import os
import sys

import nbformat

os.environ.setdefault("MPLBACKEND", "Agg")
PATH = sys.argv[1] if len(sys.argv) > 1 else "BTM_score_analysis.ipynb"
nb = nbformat.read(PATH, as_version=4)


def source(cell):
    return cell["source"] if isinstance(cell["source"], str) else "".join(cell["source"])


namespace = {"__name__": "__main__"}
selected = [c for c in nb.cells if c["cell_type"] == "code" and "core" in c.get("metadata", {}).get("tags", [])]
selected += [c for c in nb.cells if c["cell_type"] == "code" and "identity" in c.get("metadata", {}).get("tags", [])]
for cell in selected:
    code = source(cell)
    ast.parse(code)
    print(f">>> cell `{cell.get('id')}`", flush=True)
    exec(compile(code, f"<cell {cell.get('id')}>", "exec"), namespace)
print("\nIDENTITY TEST: PASSED")
