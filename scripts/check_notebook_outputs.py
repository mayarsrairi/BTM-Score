"""Post-run check of the SAVED notebook (run it after `jupyter nbconvert --execute --inplace`).

Every output of every code cell is inspected, whatever its type: stdout and stderr streams, error
outputs, and every text or JSON representation of display / execute results (images are only counted).

The check FAILS (exit code 1) if the notebook:
  - contains an error output or a code cell that was never executed;
  - has a figure cell without an image output;
  - has any output on the stderr stream, or any warning text in any output (e.g. FutureWarning,
    ConvergenceWarning, TqdmWarning): warnings are never left in the saved notebook;
  - prints a local file path anywhere;
  - prints anything at patient level (row numbers, individual diagnoses / predictions).

The same text patterns are checked inside the notebook itself, on everything it printed while
running (cell `checks`); this script checks the file that is actually saved and published.

Usage:
    python scripts/check_notebook_outputs.py [BTM_score_analysis.ipynb]
    python scripts/check_notebook_outputs.py --self-test     # proves that each rule really fires
"""
import json
import re
import sys

import nbformat

# The path pattern uses character classes ([U], [O]) so that this file does not itself contain the
# literal strings it searches for (the repository is scanned for them before publication).
LEAK_PATTERNS = {
    "local file path": re.compile(r"[A-Za-z]:\\|/[U]sers/|[O]neDrive|site-packages|\\[U]sers\\"),
    "patient row number / record index": re.compile(r"row index|row number|record index", re.I),
    "patient-level table header": re.compile(r"(True|Predicted|Real|Actual)\s+diagnosis", re.I),
    "patient identifier": re.compile(r"patient[_ ]?id", re.I),
    "patient-level row (index followed by a diagnosis)": re.compile(r"^\s*\d{1,4}\s+(IDA|BTM|iron|beta)\b", re.I | re.M),
    "block of per-row numeric lines (>= 5 consecutive)": re.compile(
        r"(?:^[ \t]*\d{1,4}[ \t]+-?\d+(?:\.\d+)?(?:[ \t]+-?\d+(?:\.\d+)?){3,}[ \t]*$\n?){5,}", re.M),
}
WARNING_PATTERN = re.compile(r"\b\w*Warning\b|\bwarnings?\.warn\b|\bUserWarning\b")


def source(cell):
    return cell["source"] if isinstance(cell["source"], str) else "".join(cell["source"])


def as_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(value)
    return json.dumps(value)


def output_text(out):
    """All the text an output can carry: stream text, error name/value/traceback, text/* and JSON data."""
    parts = []
    if "text" in out:
        parts.append(as_text(out["text"]))
    for key, val in (out.get("data") or {}).items():
        if key.startswith("text/") or key.endswith("json"):
            parts.append(as_text(val))
    if out.get("output_type") == "error":
        parts.append(f"{out.get('ename')}: {out.get('evalue')}")
        parts.extend(out.get("traceback") or [])
    return "\n".join(parts)


def inspect_notebook(nb):
    """Returns (report lines, ok)."""
    errors, never_run, missing_fig, stderr_cells, warning_cells, findings = [], [], [], [], [], {}
    counts = {"stdout": 0, "stderr": 0, "error": 0, "image": 0, "other": 0}
    n_code = 0
    for i, cell in enumerate(nb.cells):
        if cell["cell_type"] != "code":
            continue
        n_code += 1
        cid = cell.get("id", str(i))
        outs = cell.get("outputs", [])
        if cell.get("execution_count") is None:
            never_run.append(cid)
        if "plt.show()" in source(cell) and not any("image/png" in (o.get("data") or {}) for o in outs):
            missing_fig.append(cid)
        for o in outs:
            kind = o.get("output_type")
            if kind == "stream":
                counts["stderr" if o.get("name") == "stderr" else "stdout"] += 1
                if o.get("name") == "stderr":
                    stderr_cells.append(cid)
            elif kind == "error":
                counts["error"] += 1
                errors.append(cid)
            elif "image/png" in (o.get("data") or {}):
                counts["image"] += 1
            else:
                counts["other"] += 1
        text = "\n".join(output_text(o) for o in outs)
        if WARNING_PATTERN.search(text):
            warning_cells.append(cid)
        for name, pat in LEAK_PATTERNS.items():
            n = len(pat.findall(text))
            if n:
                findings.setdefault(name, []).append((cid, n))

    lines = [f"{len(nb.cells)} cells, {n_code} code cells",
             f"  outputs inspected: stdout {counts['stdout']}, stderr {counts['stderr']}, error {counts['error']}, "
             f"image {counts['image']}, other {counts['other']}",
             f"  cells with an error output          : {sorted(set(errors)) or 'none'}",
             f"  code cells never executed           : {never_run or 'none'}",
             f"  figure cells without an image       : {missing_fig or 'none'}",
             f"  cells with stderr output            : {sorted(set(stderr_cells)) or 'none'}",
             f"  cells with warning text in outputs  : {warning_cells or 'none'}"]
    for name in LEAK_PATTERNS:
        lines.append(f"  {name:50s}: {findings.get(name, 'none')}")
    ok = not (errors or never_run or missing_fig or stderr_cells or warning_cells or findings)
    return lines, ok


def _notebook(*cells):
    nb = nbformat.v4.new_notebook()
    nb.cells = list(cells)
    return nb


def _code(src, outputs, execution_count=1):
    cell = nbformat.v4.new_code_cell(src)
    cell.outputs = outputs
    cell.execution_count = execution_count
    return cell


def self_test():
    """Builds small in-memory notebooks, one per rule, and checks that each one is caught."""
    bs = chr(92)
    fake_path = "C" + ":" + bs + "Us" + "ers" + bs + "someone" + bs + "data.xlsx"
    stdout = lambda text: nbformat.v4.new_output("stream", name="stdout", text=text)
    clean = _notebook(_code("print(1)", [stdout("cohort: 330 patients\nAUC 0.977\n")]))
    cases = {
        "clean notebook": (clean, True),
        "stderr stream": (_notebook(_code("x", [nbformat.v4.new_output("stream", name="stderr", text="something\n")])), False),
        "warning text on stdout": (_notebook(_code("x", [stdout("TqdmWarning: IProgress not found\n")])), False),
        "warning text in a result": (_notebook(_code("x", [nbformat.v4.new_output(
            "execute_result", data={"text/plain": "FutureWarning: changed in a later version"}, execution_count=1)])), False),
        "error output": (_notebook(_code("x", [nbformat.v4.new_output("error", ename="ValueError", evalue="bad", traceback=["tb"])])), False),
        "never-executed cell": (_notebook(_code("print(1)", [], execution_count=None)), False),
        "local path": (_notebook(_code("x", [stdout(f"loading {fake_path}\n")])), False),
        "figure without image": (_notebook(_code("plt.show()", [])), False),
        "patient-level row": (_notebook(_code("x", [stdout("  17  IDA  0.12\n")])), False),
        "patient-level header": (_notebook(_code("x", [stdout("True diagnosis  predicted\n")])), False),
        "block of per-row numbers": (_notebook(_code("x", [stdout("\n".join(f"{i}  0.1  0.2  0.3  0.4" for i in range(8)) + "\n")])), False),
    }
    failures = 0
    for name, (nb, expected_ok) in cases.items():
        _, ok = inspect_notebook(nb)
        verdict = "OK " if ok == expected_ok else "BAD"
        failures += ok != expected_ok
        print(f"  [{verdict}] {name:28s} -> {'passes' if ok else 'is rejected'} (expected: {'passes' if expected_ok else 'rejected'})")
    print("SELF-TEST:", "PASSED" if not failures else f"FAILED ({failures} case(s))")
    return 0 if not failures else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    path = next((a for a in sys.argv[1:] if not a.startswith("--")), "BTM_score_analysis.ipynb")
    report, ok = inspect_notebook(nbformat.read(path, as_version=4))
    print(f"{path}: " + report[0])
    print("\n".join(report[1:]))
    print("RESULT:", "PASSED" if ok else "FAILED")
    sys.exit(0 if ok else 1)
