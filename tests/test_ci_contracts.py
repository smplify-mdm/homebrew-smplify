"""Exercise the actual public-tap CI scripts with synthetic scanner results."""
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SecretScanContracts(unittest.TestCase):
    def run_scan(self, scenario, mode="diff"):
        with tempfile.TemporaryDirectory(prefix="tap-ci-") as directory:
            tmp = Path(directory)
            fake = tmp / "gitleaks"
            fake.write_text(textwrap.dedent('''\
                #!/usr/bin/env bash
                case "$SCENARIO" in
                  crash) exit 42 ;;
                  missing) exit 0 ;;
                  malformed) printf '{' > "$RUNNER_TEMP/gitleaks-report.json" ;;
                  object) printf '{}' > "$RUNNER_TEMP/gitleaks-report.json" ;;
                  clean) printf '[]' > "$RUNNER_TEMP/gitleaks-report.json" ;;
                  finding) printf '[{"RuleID":"synthetic"}]' > "$RUNNER_TEMP/gitleaks-report.json" ;;
                esac
            '''))
            fake.chmod(0o755)
            output = tmp / "output"
            # Even a clean-looking stale report cannot stand in for a new scan.
            (tmp / "gitleaks-report.json").write_text("[]")
            env = dict(os.environ, RUNNER_TEMP=directory, GITHUB_OUTPUT=str(output),
                       MODE=mode, LOG_OPTS="base..head", SCENARIO=scenario)
            result = subprocess.run(["bash", str(ROOT / "scripts/secret-scan.sh")],
                                    cwd=ROOT, env=env, text=True, capture_output=True, timeout=5)
            return result.returncode, output.read_text() if output.exists() else "", result.stderr

    def test_failed_scanner_and_untrustworthy_reports_fail_closed(self):
        for scenario in ("crash", "missing", "malformed", "object"):
            with self.subTest(scenario=scenario):
                code, output, _ = self.run_scan(scenario)
                self.assertNotEqual(code, 0)
                self.assertNotIn("count=0", output)

    def test_clean_and_finding_counts_reach_the_existing_policy_gate(self):
        for mode in ("diff", "full"):
            with self.subTest(mode=mode):
                self.assertEqual(self.run_scan("clean", mode)[:2], (0, "count=0\n"))
                self.assertEqual(self.run_scan("finding", mode)[:2], (0, "count=1\n"))
        workflow = (ROOT / ".github/workflows/secrets.yml").read_text()
        self.assertIn("steps.plan.outputs.mode == 'diff' && steps.scan.outputs.count != '0'", workflow)

    def test_failed_scan_summary_says_unknown_not_no_findings(self):
        workflow = (ROOT / ".github/workflows/secrets.yml").read_text()
        section = workflow.split("      - name: Write job summary\n", 1)[1].split("      - name:", 1)[0]
        script = textwrap.dedent(section.split("        run: |\n", 1)[1])
        with tempfile.TemporaryDirectory(prefix="tap-summary-") as directory:
            summary = Path(directory) / "summary"
            env = dict(os.environ, SCAN_OUTCOME="failure", MODE="diff", COUNT="",
                       GITHUB_STEP_SUMMARY=str(summary), RUNNER_TEMP=directory)
            result = subprocess.run(["bash", "-c", script], cwd=ROOT, env=env,
                                    text=True, capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("findings are unknown", summary.read_text())
            self.assertNotIn("No findings.", summary.read_text())


class TitleContracts(unittest.TestCase):
    def test_conventional_title_and_fork_input_are_treated_as_data(self):
        with tempfile.TemporaryDirectory(prefix="tap-title-") as directory:
            marker = Path(directory) / "injected"
            for title, author, expected in (("fix(SMP-1369): repair public CI", "fixture", 0),
                                            ("ordinary words", "fixture", 1),
                                            (f"$(touch {marker})", "fixture", 1),
                                            ("dependency update", "dependabot[bot]", 0)):
                with self.subTest(title=title):
                    result = subprocess.run(["bash", str(ROOT / "scripts/pr-title.sh")], cwd=ROOT,
                                            env=dict(os.environ, TITLE=title, AUTHOR=author),
                                            text=True, capture_output=True, timeout=5)
                    self.assertEqual(result.returncode, expected)
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
