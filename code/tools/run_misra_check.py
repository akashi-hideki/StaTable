#!/usr/bin/env python3
"""
MISRA C check for StaTable-generated code (v2).

Parses cppcheck XML output (from either stdout or stderr) and
produces a Markdown summary.

Informational only. Never fails the build.
"""
import argparse
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path


def collect_c_files(root: Path):
    return sorted(root.rglob('*.c'))


def build_cppcheck_command(c_files, include_dirs, suppressions_file,
                           addon_dir=None):
    cmd = [
        'cppcheck',
        '--enable=warning,style,performance,portability',
        '--inline-suppr',
        '--error-exitcode=0',
        '--xml',
        '--xml-version=2',
        '--quiet',
    ]

    # MISRA addon: prefer an explicit directory (used in CI, where
    # the addon is fetched from the matching cppcheck tag).  Fall
    # back to cppcheck's built-in search path ("misra").
    if addon_dir:
        addon_file = Path(addon_dir) / 'misra.py'
        if not addon_file.exists():
            print(
                f'WARN: {addon_file} not found; falling back to '
                'cppcheck built-in addon search.',
                file=sys.stderr,
            )
            cmd.append('--addon=misra')
        else:
            cmd.append(f'--addon={addon_file}')
    else:
        cmd.append('--addon=misra')

    if suppressions_file and suppressions_file.exists():
        cmd.append(f'--suppressions-list={suppressions_file}')
    for inc in include_dirs:
        cmd += ['-I', str(inc)]
    cmd += [str(f) for f in c_files]
    return cmd


def find_xml(stdout: str, stderr: str) -> str:
    """Return whichever stream contains valid XML."""
    for candidate in (stderr, stdout):
        if candidate and candidate.lstrip().startswith('<?xml'):
            return candidate
    return ''


def parse_xml(xml_text: str):
    """Return (misra_counter, non_misra_counter, error_samples)."""
    misra = Counter()
    non_misra = Counter()
    samples = defaultdict(list)

    if not xml_text.strip():
        return misra, non_misra, samples

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f'WARN: XML parse error: {e}', file=sys.stderr)
        return misra, non_misra, samples

    for err in root.iter('error'):
        err_id = err.get('id', '')
        severity = err.get('severity', '')
        msg = err.get('msg', '')
        if err_id.startswith('misra-c2012-'):
            rule = err_id.replace('misra-c2012-', '')
            misra[rule] += 1
        elif err_id == 'misra-config':
            # informational; skip
            continue
        else:
            non_misra[err_id] += 1
            if len(samples[err_id]) < 3:
                samples[err_id].append(msg)

    return misra, non_misra, samples


def write_summary(out_dir, c_files, misra, non_misra, samples):
    total_misra = sum(misra.values())
    lines = [
        '# MISRA C Check Summary',
        '',
        '> **Informational only.** This report does not fail the build.',
        '> cppcheck + MISRA addon is not a certified MISRA checker.',
        '',
        '## Overview',
        '',
        f'- Files analyzed: {len(c_files)}',
        f'- Total MISRA rule hits: {total_misra}',
        f'- Distinct MISRA rules hit: {len(misra)}',
        f'- Non-MISRA warnings: {sum(non_misra.values())}',
        '',
    ]

    if misra:
        lines += [
            '## MISRA rules (by frequency)',
            '',
            '| Rule | Count |',
            '|------|------:|',
        ]
        for rule, count in misra.most_common():
            lines.append(f'| misra-c2012-{rule} | {count} |')
        lines.append('')

    if non_misra:
        lines += [
            '## Non-MISRA warnings (by frequency)',
            '',
            '| ID | Count | Sample message |',
            '|----|------:|----------------|',
        ]
        for warn_id, count in non_misra.most_common():
            sample = samples[warn_id][0] if samples[warn_id] else ''
            sample = sample.replace('|', '\\|')[:80]
            lines.append(f'| {warn_id} | {count} | {sample} |')
        lines.append('')

    lines += [
        '## Artifacts',
        '',
        '- `cppcheck_raw.xml` — cppcheck XML (extracted from stdout or stderr)',
        '- `cppcheck_stdout.txt` — raw stdout (may be empty)',
        '- `cppcheck_stderr.txt` — raw stderr (may be empty; cppcheck 2.21 emits XML here)',
        '',
        '## Next Steps',
        '',
        '1. Review top rules above.',
        '2. Add justified suppressions to `misra/suppressions.txt`.',
        '3. Record progress in `misra/baseline.md`.',
        '',
    ]
    (out_dir / 'summary.md').write_text('\n'.join(lines), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--suppressions', default='misra/suppressions.txt')
    parser.add_argument(
        '--addon-dir',
        default=None,
        help=("Directory containing misra.py and misra_9.py. "
              "If omitted, cppcheck's built-in addon search is used."),
    )
    args = parser.parse_args()

    root = Path(args.root)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not root.exists():
        print(f'ERROR: root not found: {root}', file=sys.stderr)
        return 1

    c_files = collect_c_files(root)
    if not c_files:
        print('No .c files found.')
        write_summary(out_dir, [], Counter(), Counter(), {})
        return 0

    print(f'Found {len(c_files)} C file(s)')

    include_dirs = [root / 'include', root / 'common', root / 'src']
    include_dirs = [d for d in include_dirs if d.exists()]
    suppressions = Path(args.suppressions)

    cmd = build_cppcheck_command(
        c_files, include_dirs, suppressions, addon_dir=args.addon_dir)

    # Guard: cppcheck rejects suppressions files with a UTF-8 BOM.
    # The BOM is parsed as part of the first rule id (e.g.
    # "misra-c2012-2.3" -> invalid id) and cppcheck aborts before
    # emitting any XML.
    if suppressions.exists():
        head = suppressions.read_bytes()[:3]
        if head == b'\xef\xbb\xbf':
            print(
                f'WARN: {suppressions} starts with a UTF-8 BOM; '
                'cppcheck will reject the first suppression. '
                'Re-save the file without BOM.',
                file=sys.stderr,
            )

    print('Running cppcheck...')

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=600,
        )
    except FileNotFoundError:
        print('ERROR: cppcheck is not installed.', file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired:
        print('ERROR: cppcheck timed out.', file=sys.stderr)
        return 1

    stdout = result.stdout or ''
    stderr = result.stderr or ''

    # cppcheck 2.21 emits XML to stderr; older versions to stdout.
    # find_xml() picks whichever stream carries valid XML.
    xml_text = find_xml(stdout, stderr)

    # Canonical XML (non-empty regardless of which stream carried it)
    (out_dir / 'cppcheck_raw.xml').write_text(xml_text, encoding='utf-8')
    # Raw streams preserved for diagnostics
    (out_dir / 'cppcheck_stdout.txt').write_text(stdout, encoding='utf-8')
    (out_dir / 'cppcheck_stderr.txt').write_text(stderr, encoding='utf-8')

    misra, non_misra, samples = parse_xml(xml_text)

    write_summary(out_dir, c_files, misra, non_misra, samples)

    print(f'MISRA rule hits: {sum(misra.values())} '
          f'across {len(misra)} distinct rules')
    print(f'Non-MISRA warnings: {sum(non_misra.values())}')
    print(f'Report: {out_dir / "summary.md"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())