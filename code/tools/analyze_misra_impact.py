#!/usr/bin/env python3
"""
MISRA Impact Analyzer for StaTable.

Reads cppcheck XML output and determines which codegen/ source files
need modification for each MISRA violation.

Informational only. Never fails the build.

Usage:
    python tools/analyze_misra_impact.py \
        --xml misra_report/cppcheck_raw.xml \
        --out misra_report/impact.md
"""
import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict, Counter
from pathlib import Path


# ======================================================================
# Mapping: generated file pattern -> codegen source file(s)
# ======================================================================
# Keys are substrings that appear in generated C file paths.
# Order matters: first match wins.
GENERATED_TO_CODEGEN = [
    ('statable_role_functions', [
        'codegen/role_function_generator.py',
        'codegen/code_templates.py',
    ]),
    ('statable_transitions', [
        'codegen/transition_generator.py',
        'codegen/code_templates.py',
    ]),
    ('statable_types', [
        'codegen/struct_generator.py',
        'codegen/enum_generator.py',
        'codegen/variable_generator.py',
        'codegen/code_templates.py',
    ]),
    ('statable_init', [
        'codegen/variable_generator.py',
        'codegen/c_code_generator.py',
    ]),
    ('statable_event_queue', [
        'codegen/event_queue_generator.py',
    ]),
    ('statable_interrupt', [
        'codegen/interrupt_generator.py',
    ]),
    ('statable_timer', [
        'codegen/timer_generator.py',
    ]),
    ('osal', [
        'codegen/osal_generator.py',
        'codegen/code_templates.py',
    ]),
    ('statable_all', [
        'codegen/c_code_generator.py',  # super_include steps
    ]),
    ('_run.c', [
        'codegen/c_code_generator.py',  # super_loop steps
    ]),
]

# Rules we classify as "non-actionable for codegen" (informational only)
EXCLUDED_RULE_IDS = {
    'misra-config',
}

# Rules that are suppressed by design (documented in misra/suppressions.txt)
SUPPRESSED_RULES = {
    'misra-c2012-8.4',
    'misra-c2012-8.7',
    'misra-c2012-8.9',
    'misra-c2012-5.9',
    'misra-c2012-15.5',
    'misra-c2012-15.7',
    'misra-c2012-2.3',
    'misra-c2012-2.4',
    'misra-c2012-2.5',
    'misra-c2012-21.6',
}

# Non-MISRA cppcheck warning IDs we track
NON_MISRA_IDS = {
    'unreadVariable',
    'knownConditionTrueFalse',
    'variableScope',
    'constVariablePointer',
}


# ======================================================================
# Parsing
# ======================================================================
def load_xml(path: Path) -> str:
    if not path.exists():
        print(f'ERROR: XML not found: {path}', file=sys.stderr)
        sys.exit(1)
    text = path.read_text(encoding='utf-8')
    if not text.lstrip().startswith('<?xml'):
        # maybe the file is empty; try the stderr counterpart
        alt = path.parent / 'cppcheck_stderr.txt'
        if alt.exists():
            text = alt.read_text(encoding='utf-8')
    return text


def parse_errors(xml_text: str):
    """Yield dicts of {file, rule_id, severity, msg, line}."""
    root = ET.fromstring(xml_text)
    for err in root.iter('error'):
        err_id = err.get('id', '')
        if err_id in EXCLUDED_RULE_IDS:
            continue
        severity = err.get('severity', '')
        msg = err.get('msg', '')
        for loc in err.findall('location'):
            f = loc.get('file', '')
            line = loc.get('line', '')
            if f:
                yield {
                    'file': f,
                    'rule_id': err_id,
                    'severity': severity,
                    'msg': msg,
                    'line': line,
                }


# ======================================================================
# Mapping
# ======================================================================
def classify_rule(rule_id: str) -> str:
    if rule_id.startswith('misra-c2012-'):
        if rule_id in SUPPRESSED_RULES:
            return 'suppressed'
        return 'misra-active'
    if rule_id in NON_MISRA_IDS:
        return 'non-misra'
    return 'other'


def map_to_codegen(generated_file: str) -> list:
    """Return list of codegen source paths responsible for this file."""
    normalized = generated_file.replace('\\', '/')
    for pattern, sources in GENERATED_TO_CODEGEN:
        if pattern in normalized:
            return sources
    return ['codegen/c_code_generator.py']  # fallback


# ======================================================================
# Report
# ======================================================================
def build_report(errors):
    """
    Returns:
        by_codegen: {codegen_path: Counter(rule_id)}
        by_rule:    {rule_id: Counter(codegen_path)}
        totals:     Counter(category)
    """
    by_codegen = defaultdict(Counter)
    by_rule = defaultdict(Counter)
    totals = Counter()

    for e in errors:
        rule = e['rule_id']
        cat = classify_rule(rule)
        totals[cat] += 1

        if cat == 'suppressed':
            continue

        sources = map_to_codegen(e['file'])
        for src in sources:
            by_codegen[src][rule] += 1
            by_rule[rule][src] += 1

    return by_codegen, by_rule, totals


def write_markdown(out_path: Path, by_codegen, by_rule, totals):
    lines = [
        '# MISRA Impact Analysis',
        '',
        '> Informational only. This report does not fail the build.',
        '> Shows which `codegen/` source files are responsible for',
        '> each MISRA violation detected in generated C code.',
        '',
        '## Totals by category',
        '',
        '| Category | Count |',
        '|----------|------:|',
    ]
    for cat in ('misra-active', 'non-misra', 'suppressed', 'other'):
        if totals[cat]:
            lines.append(f'| {cat} | {totals[cat]} |')
    lines.append('')

    # --- by codegen source ---
    lines += [
        '## Codegen sources to modify (ranked)',
        '',
        '| Codegen source | Total hits | Top rules |',
        '|----------------|-----------:|-----------|',
    ]
    ranked = sorted(
        by_codegen.items(),
        key=lambda kv: sum(kv[1].values()),
        reverse=True,
    )
    for src, rules in ranked:
        total = sum(rules.values())
        top = ', '.join(f'{r}({c})' for r, c in rules.most_common(3))
        lines.append(f'| `{src}` | {total} | {top} |')
    lines.append('')

    # --- by rule ---
    lines += [
        '## Rules to address (ranked)',
        '',
        '| Rule | Total | Responsible codegen |',
        '|------|------:|---------------------|',
    ]
    for rule, srcs in sorted(
        by_rule.items(),
        key=lambda kv: sum(kv[1].values()),
        reverse=True,
    ):
        total = sum(srcs.values())
        owners = ', '.join(f'`{s}`' for s, _ in srcs.most_common(3))
        lines.append(f'| {rule} | {total} | {owners} |')
    lines.append('')

    # --- actionable plan ---
    lines += [
        '## Suggested action order',
        '',
        'Based on frequency and estimated fix effort:',
        '',
    ]
    action_order = [
        ('misra-c2012-17.3', 'Add missing includes in generated .c files'),
        ('misra-c2012-17.7', 'Add (void) cast to RoleFunc_* calls'),
        ('unreadVariable', 'Add (void)var; for generated locals'),
        ('knownConditionTrueFalse', 'Review _handled logic in cell functions'),
        ('misra-c2012-12.1', 'Add parentheses around operator expressions'),
        ('variableScope', 'Reduce _handled variable scope'),
        ('misra-c2012-11.5', 'Add explicit casts in osal.c'),
        ('misra-c2012-18.4', 'Review pointer arithmetic in osal.c'),
        ('misra-c2012-10.4', 'Check type mismatch in statable_timer.c'),
    ]
    lines += ['| # | Rule | Action | Hits |',
              '|---|------|--------|-----:|']
    for i, (rule, action) in enumerate(action_order, 1):
        hits = sum(by_rule.get(rule, {}).values())
        lines.append(f'| {i} | {rule} | {action} | {hits} |')
    lines.append('')

    # --- suppressed rules ---
    lines += [
        '## Suppressed by design',
        '',
        'The following rules are suppressed in `misra/suppressions.txt`.',
        '',
    ]
    if totals['suppressed']:
        lines.append(f'- Suppressed hits: {totals["suppressed"]}')
    lines.append('')

    out_path.write_text('\n'.join(lines), encoding='utf-8')


def write_csv(out_path: Path, by_codegen):
    with out_path.open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['codegen_source', 'rule_id', 'count'])
        for src, rules in by_codegen.items():
            for rule, count in rules.items():
                w.writerow([src, rule, count])


# ======================================================================
# Main
# ======================================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--xml', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--csv', default='')
    args = parser.parse_args()

    xml_path = Path(args.xml)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    xml_text = load_xml(xml_path)
    errors = list(parse_errors(xml_text))
    print(f'Parsed {len(errors)} error records (excluding misra-config)')

    by_codegen, by_rule, totals = build_report(errors)
    write_markdown(out_path, by_codegen, by_rule, totals)
    print(f'Report: {out_path}')

    if args.csv:
        csv_path = Path(args.csv)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        write_csv(csv_path, by_codegen)
        print(f'CSV:    {csv_path}')

    print()
    print('Summary:')
    for cat in ('misra-active', 'non-misra', 'suppressed', 'other'):
        if totals[cat]:
            print(f'  {cat}: {totals[cat]}')

    print()
    print('Top codegen sources to modify:')
    ranked = sorted(
        by_codegen.items(),
        key=lambda kv: sum(kv[1].values()),
        reverse=True,
    )
    for src, rules in ranked[:5]:
        total = sum(rules.values())
        print(f'  {src}: {total}')


if __name__ == '__main__':
    sys.exit(main())