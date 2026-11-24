"""Run from anywhere inside a checkout containing this practical-3 folder."""
import json
import os
from pathlib import Path
import subprocess
import sys

here = Path(__file__).resolve().parent
repo = here.parent
out = here / "results"
out.mkdir(exist_ok=True)
src = repo / "src"
if not (src / "requests" / "models.py").is_file():
    sys.exit("Place practical-3 in the root of the Requests checkout.")
env = {**os.environ, "PYTHONPATH": str(src), "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
coverage = [sys.executable, "-m", "coverage"]
cfg = "--rcfile=" + str(here / "coverage.ini")
baseline = [
    "tests/test_requests.py::test_prepared_copy",
    "tests/test_requests.py::TestRequests::test_prepare_request_with_bytestring_url",
]
new = ["practical-3/test_prepared.py"]
first = " or ".join(["test_prepared_copy", "test_prepare_request_with_bytestring_url",
                     "query_order", "idna_host", "invalid_url", "form_repeated_values",
                     "large_body", "empty_body", "json_custom_type", "multipart_fields"])
stages = {"before": baseline, "first": baseline + new + ["-k", first],
          "new_only": new, "after": baseline + new}
summary = {}
for stage, targets in stages.items():
    env["COVERAGE_FILE"] = str(out / (".coverage-" + stage))
    def run(args):
        subprocess.run(coverage + args, cwd=repo, env=env, check=True)
    run(["run", cfg, "-m", "pytest", "-q", "-o", "addopts=", *targets])
    dest = out / (stage + ".json")
    run(["json", cfg, "-o", str(dest)])
    measured = json.loads(dest.read_text(encoding="utf-8"))["files"]
    model = next(data for path, data in measured.items()
                 if Path(path).as_posix().endswith("requests/models.py"))
    region = model["classes"]["PreparedRequest"]
    counts = region["summary"]
    line_pct = 100 * counts["covered_lines"] / counts["num_statements"]
    branch_pct = 100 * counts["covered_branches"] / counts["num_branches"]
    summary[stage] = {"lines": counts["covered_lines"], "total_lines": counts["num_statements"],
                      "line_percent": round(line_pct, 2), "branches": counts["covered_branches"],
                      "total_branches": counts["num_branches"], "branch_percent": round(branch_pct, 2),
                      "missing_lines": region["missing_lines"]}
    print(f"{stage}: lines {line_pct:.2f}%, branches {branch_pct:.2f}%", flush=True)
run(["html", cfg, "-d", str(out / "html")])
(out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
