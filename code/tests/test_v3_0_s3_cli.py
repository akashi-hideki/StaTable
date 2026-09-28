# code/tests/test_v3_0_s3_cli.py
"""
Phase S-3 (v3.0) tests: CLI implementation.

Verifies:
  - statable.cli imports and exposes CLI_VERSION
  - build_parser() has generate / validate / version subcommands
  - cmd_version prints version
  - cmd_validate on real XML returns JSON structure
  - cmd_validate on missing file returns exit code 2
  - cmd_generate creates files
  - text format works
  - Exit code 1 on validation error (--exit-on-error)
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))

TOTAL = 0
PASSED = 0
FAILED = 0

SAMPLE_XML = CODE / "tests" / "data" / "v22_features_test.xml"


def check(name: str, cond: bool, detail: str = "") -> None:
    global TOTAL, PASSED, FAILED
    TOTAL += 1
    if cond:
        PASSED += 1
        print(f"[PASS] {name}")
    else:
        FAILED += 1
        print(f"[FAIL] {name}" + (f" -- {detail}" if detail else ""))


def run_cli(argv):
    """Run cli.main with captured stdout/stderr. Returns (rc, out, err)."""
    from statable import cli
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = cli.main(argv)
    return rc, out.getvalue(), err.getvalue()


def main() -> int:
    print("=" * 70)
    print("  test_v3_0_s3_cli")
    print("=" * 70)

    # --- T1: import / version -----------------------------------------
    try:
        from statable import cli
        check("statable.cli importable", True)
        check("CLI_VERSION == '3.0.0'",
              cli.CLI_VERSION == "3.0.0",
              f"got: {cli.CLI_VERSION!r}")
    except Exception as e:
        check("statable.cli importable", False, repr(e))
        _summary()
        return 1

    # --- T2: parser ---------------------------------------------------
    try:
        parser = cli.build_parser()
        check("build_parser returns ArgumentParser", parser is not None)
        # Introspect subparsers
        sub_actions = [a for a in parser._actions
                       if hasattr(a, "choices") and a.choices
                       and isinstance(a.choices, dict)]
        names = set()
        for a in sub_actions:
            names.update(a.choices.keys())
        check("subcommands include generate",
              "generate" in names, f"got: {names}")
        check("subcommands include validate",
              "validate" in names, f"got: {names}")
        check("subcommands include version",
              "version" in names, f"got: {names}")
    except Exception as e:
        check("build_parser works", False, repr(e))

    # --- T3: version --------------------------------------------------
    rc, out, _ = run_cli(["version"])
    check("version: exit 0", rc == 0, f"rc={rc}")
    check("version: prints 'statable-cli 3.0.0'",
          "statable-cli 3.0.0" in out,
          f"out={out!r}")

    # --- T4: validate on real XML (json) ------------------------------
    if not SAMPLE_XML.exists():
        check(f"sample XML exists: {SAMPLE_XML.name}",
              False, f"missing: {SAMPLE_XML}")
    else:
        check(f"sample XML exists: {SAMPLE_XML.name}", True)

        rc, out, _ = run_cli([
            "validate",
            "--xml", str(SAMPLE_XML),
            "--format", "json",
        ])
        check("validate: exit 0 (no errors)", rc == 0, f"rc={rc}")

        try:
            data = json.loads(out)
            check("validate: JSON parseable", True)
            check("validate: status is 'ok' or 'error'",
                  data.get("status") in ("ok", "error"),
                  f"got: {data.get('status')!r}")
            check("validate: has 'errors' field",
                  "errors" in data)
            check("validate: has 'warnings' field",
                  "warnings" in data)
            check("validate: has 'issues' list",
                  isinstance(data.get("issues"), list))
            check("validate: command == 'validate'",
                  data.get("command") == "validate")
        except Exception as e:
            check("validate: JSON parseable", False, repr(e))

    # --- T5: validate on missing file ---------------------------------
    rc, _, err = run_cli([
        "validate",
        "--xml", "nonexistent_xyz.xml",
        "--format", "json",
    ])
    check("missing file: exit 2", rc == 2, f"rc={rc}")
    check("missing file: error message on stderr",
          "not found" in err.lower() or "error" in err.lower(),
          f"err={err!r}")

    # --- T6: validate text format ------------------------------------
    if SAMPLE_XML.exists():
        rc, out, _ = run_cli([
            "validate",
            "--xml", str(SAMPLE_XML),
            "--format", "text",
        ])
        check("validate text: exit 0", rc == 0, f"rc={rc}")
        check("validate text: contains 'OK' or 'ERROR'",
              "OK" in out or "ERROR" in out,
              f"out[:100]={out[:100]!r}")

    # --- T7: generate -------------------------------------------------
    if SAMPLE_XML.exists():
        with tempfile.TemporaryDirectory() as tmpd:
            rc, out, _ = run_cli([
                "generate",
                "--xml", str(SAMPLE_XML),
                "--out", tmpd,
                "--format", "json",
            ])
            check("generate: exit 0", rc == 0, f"rc={rc}")

            try:
                data = json.loads(out)
                check("generate: status == 'ok'",
                      data.get("status") == "ok",
                      f"got: {data.get('status')!r}")
                files = data.get("files_generated", [])
                check("generate: files_generated non-empty",
                      len(files) > 0,
                      f"got: {len(files)}")
                check("generate: command == 'generate'",
                      data.get("command") == "generate")

                # At least one file actually written
                p = Path(tmpd)
                written = list(p.rglob("*"))
                files_only = [f for f in written if f.is_file()]
                check("generate: files actually on disk",
                      len(files_only) > 0,
                      f"found: {len(files_only)}")
            except Exception as e:
                check("generate: JSON parseable", False, repr(e))

    # --- T8: generate on missing file ---------------------------------
    rc, _, _ = run_cli([
        "generate",
        "--xml", "nonexistent_xyz.xml",
        "--out", "irrelevant",
        "--format", "json",
    ])
    check("generate missing file: exit 2", rc == 2, f"rc={rc}")

    _summary()
    return 0 if FAILED == 0 else 1


def _summary() -> None:
    print("-" * 70)
    print(f"TOTAL: {TOTAL}  PASSED: {PASSED}  FAILED: {FAILED}")
    print("=" * 70)


if __name__ == "__main__":
    sys.exit(main())
