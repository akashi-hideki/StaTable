#!/usr/bin/env python3
"""
Search tool to identify affected files for StaTable v2.2 changes.

Features:
  - Keyword search across all .py files (line numbers)
  - Import graph analysis (forward / reverse)
  - Symbol definition / reference tracking
  - Missing module detection (imported but not shared)
  - Multiple output formats: text / json / markdown

Usage:
  python tools/find_affected_files.py                     # default keywords
  python tools/find_affected_files.py --keyword "early_return"
  python tools/find_affected_files.py --imports-of "statable.state_machine"
  python tools/find_affected_files.py --symbol "Transition"
  python tools/find_affected_files.py --shared "statable/model.py,..."
"""

import argparse
import ast
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional


SKIP_DIRS = {".venv", "venv", "__pycache__", ".git", "node_modules"}
SKIP_PREFIXES = ("_backup_",)


@dataclass
class FileAnalysis:
    path: str
    imports: List[str] = field(default_factory=list)
    from_imports: List[Tuple[str, List[str]]] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    keywords: Dict[str, List[int]] = field(default_factory=dict)
    error: str = ""


class Analyzer:
    def __init__(self, root: str, keywords: List[str]):
        self.root = Path(root)
        self.keywords = keywords
        self.files: List[FileAnalysis] = []
        self.import_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_import: Dict[str, Set[str]] = defaultdict(set)
        self.symbol_defs: Dict[str, List[str]] = defaultdict(list)
        self.symbol_refs: Dict[str, List[str]] = defaultdict(list)

    def analyze(self) -> None:
        for path in sorted(self.root.rglob("*.py")):
            rel_parts = path.relative_to(self.root).parts
            if any(p in SKIP_DIRS or p.startswith(SKIP_PREFIXES) for p in rel_parts):
                continue
            self._analyze_file(path, str(path.relative_to(self.root)))

    def _analyze_file(self, path: Path, rel: str) -> None:
        try:
            source = path.read_text(encoding="utf-8")
        except Exception as e:
            self.files.append(FileAnalysis(path=rel, error=str(e)))
            return

        fa = FileAnalysis(path=rel)
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            fa.error = f"SyntaxError: {e}"
            self.files.append(fa)
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    fa.imports.append(alias.name)
                    self.import_graph[rel].add(alias.name)
                    self.reverse_import[alias.name].add(rel)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [a.name for a in node.names]
                fa.from_imports.append((module, names))
                if module:
                    self.import_graph[rel].add(module)
                    self.reverse_import[module].add(rel)
            elif isinstance(node, ast.ClassDef):
                fa.classes.append(node.name)
                self.symbol_defs[node.name].append(rel)
            elif isinstance(node, ast.FunctionDef):
                fa.functions.append(node.name)
                self.symbol_defs[node.name].append(rel)

        lines = source.splitlines()
        for i, line in enumerate(lines, start=1):
            for kw in self.keywords:
                if kw in line:
                    fa.keywords.setdefault(kw, []).append(i)

        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                self.symbol_refs[node.id].append(rel)

        self.files.append(fa)

    # -------- reports --------
    def report_keywords(self) -> str:
        lines = ["=== Keyword hits ==="]
        for kw in self.keywords:
            hit_files = [fa for fa in self.files if kw in fa.keywords]
            if not hit_files:
                continue
            lines.append(f"\n-- '{kw}'  ({len(hit_files)} files) --")
            for fa in sorted(hit_files, key=lambda f: f.path):
                nums = fa.keywords[kw]
                sample = ", ".join(str(n) for n in nums[:8])
                extra = f" ... (+{len(nums) - 8})" if len(nums) > 8 else ""
                lines.append(f"  {fa.path}   (lines: {sample}{extra})")
        return "\n".join(lines)

    def report_imports_of(self, module: str) -> str:
        users = sorted(self.reverse_import.get(module, set()))
        if not users:
            return f"No file imports '{module}'"
        return f"=== Files importing '{module}' ({len(users)}) ===\n" + \
               "\n".join(f"  {u}" for u in users)

    def report_symbol(self, sym: str) -> str:
        defs = sorted(set(self.symbol_defs.get(sym, [])))
        refs = sorted(set(self.symbol_refs.get(sym, [])))
        out = [f"=== Symbol '{sym}' ==="]
        out.append("  Defined in:")
        for d in defs:
            out.append(f"    {d}")
        out.append("  Referenced in:")
        for r in refs:
            out.append(f"    {r}")
        return "\n".join(out)

    def report_missing_modules(self, shared: Set[str]) -> str:
        all_imports: Set[str] = set()
        for fa in self.files:
            for m in fa.imports:
                all_imports.add(m)
            for m, _ in fa.from_imports:
                if m:
                    all_imports.add(m)

        internal = set()
        for m in all_imports:
            root = m.split(".")[0]
            if root in ("statable", "statable_gui", "codegen", "tools"):
                internal.add(m)

        # Build known-module set from shared paths
        known = set()
        for sp in shared:
            # statable/model.py -> statable.model
            mod = sp.replace("/", ".").replace("\\", ".").removesuffix(".py")
            mod = mod.removesuffix(".__init__")
            known.add(mod)
            # also add submodules
            parts = mod.split(".")
            for i in range(1, len(parts) + 1):
                known.add(".".join(parts[:i]))

        missing = sorted(m for m in internal if m not in known)

        out = [f"=== Internal modules NOT in shared set ({len(missing)}) ==="]
        if not missing:
            out.append("  (none)")
        for m in missing:
            users = sorted(self.reverse_import.get(m, set()))
            out.append(f"  {m}")
            for u in users:
                out.append(f"      <- {u}")
        return "\n".join(out)

    def to_json(self) -> str:
        data = {
            "files": [asdict(fa) for fa in self.files],
            "reverse_import": {k: sorted(v)
                               for k, v in self.reverse_import.items()},
            "symbol_defs": {k: v for k, v in self.symbol_defs.items()},
        }
        return json.dumps(data, ensure_ascii=False, indent=2)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--keyword", action="append", default=[])
    p.add_argument("--imports-of", default=None)
    p.add_argument("--symbol", default=None)
    p.add_argument("--shared", default=None,
                   help="Comma-separated list of already-shared files")
    p.add_argument("--output", default="text",
                   choices=["text", "json"])
    args = p.parse_args()

    default_keywords = [
        "early_return", "_handled",
        "has_else", "else_target",
        "pre_actions", "else_actions",
        "shared_condition", "exclusive",
        "TransitionStep", "ActionStep", "TransitionCell", "TransitionRelation",
        "TransitionContext_t",
        "StateMachine_Process",
        "generate_transition_cell_functions",
    ]
    keywords = args.keyword or default_keywords

    an = Analyzer(args.root, keywords)
    an.analyze()

    if args.output == "json":
        print(an.to_json())
        return

    print(an.report_keywords())
    print()
    if args.imports_of:
        print(an.report_imports_of(args.imports_of))
        print()
    if args.symbol:
        print(an.report_symbol(args.symbol))
        print()
    if args.shared:
        shared = set(s.strip() for s in args.shared.split(",") if s.strip())
        print(an.report_missing_modules(shared))


if __name__ == "__main__":
    main()