# StaTable CLI Guide

`statable-cli` provides command-line access to code generation and
validation, without launching the GUI.

## Installation

    pip install statable           # SDK + CLI
    pip install "statable[gui]"    # GUI included

## Subcommands

### `version`

    statable-cli version
    statable-cli --version

### `generate`

Generate C code from a design XML file.

    statable-cli generate --xml design.xml --out generated/ --format json

Options:
  --xml PATH     Input design XML (required)
  --out DIR      Output directory (required)
  --format       json (default) or text

### `validate`

Validate a design XML file.

    statable-cli validate --xml design.xml --format json --exit-on-error

Options:
  --xml PATH         Input design XML (required)
  --format           json (default) or text
  --exit-on-error    Return exit code 1 when validation fails

## Exit Codes

| Code | Meaning |
|:---:|------|
| 0 | Success |
| 1 | Validation error (with `--exit-on-error`) |
| 2 | Internal error (missing file, parse failure, etc.) |

## Output

- `--format json`: machine-readable JSON on stdout
- `--format text`: human-readable summary
- Logs and errors: stderr

## Examples

### Generate and pipe JSON to jq

    statable-cli generate --xml design.xml --out build/ --format json | jq .

### CI usage: validate and fail the build on errors

    statable-cli validate --xml design.xml --format json --exit-on-error

### Eclipse External Tools

Location: `C:\Python313\Scripts\statable-cli.exe`

Arguments:
    generate --xml ${resource_loc} --out ${project_loc}/generated --format json

## See also

- SDK API Reference: `docs/SPEC_SDK_API_ja.md` / `_en.md` (section 2.6)
- Example script: `examples/quickstart.py`
