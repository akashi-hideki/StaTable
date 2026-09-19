#!/usr/bin/env python3
"""
Detect internal modules that are imported but NOT in the shared file list.

Usage:
    python tools/find_missing_files.py --shared shared.txt
    python tools/find_missing_files.py --shared shared.txt --output json
    python tools/find_missing_files.py --list-shared    # list all internal modules
"""

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


SKIP_DIRS = {".venv", "venv", "__pycache__", ".git", "node_modules"}
SKIP_PREFIXES = ("_backup_",)
INTERNAL_ROOTS = {"statable", "statable_gui", "codegen", "tools"}


class ImportAnalyzer:
    def __init__(self, root: str):
        self.root = Path(root)
        self.all_modules: Set[str] = set()
        self.import_graph: Dict[str, Set[str]] = {}
        self.reverse: Dict[str, Set[str]] = {}

    def scan(self):
        for path in sorted(self.root.rglob("*.py")):
            parts = path.relative_to(self.root).parts
            if any(p in SKIP_DIRS or p.startswith(SKIP_PREFIXES) for p in parts):
                continue
            rel = str(path.relative_to(self.root))
            module = self._to_module(rel)
            self.all_modules.add(module)

            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except Exception:
                continue

            imports: Set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Resolve relative imports (level>0) using parent package
                        if node.level and node.level > 0:
                            parent = module.rsplit(".", node.level)[0]
                            imports.add(f"{parent}.{node.module}"
                                        if node.module else parent)
                        else:
                            imports.add(node.module)
            self.import_graph[module] = imports
            for imp in imports:
                self.reverse.setdefault(imp, set()).add(module)

    def _to_module(self, rel_path: str) -> str:
        m = rel_path.replace("/", ".").replace("\\", ".")
        m = m.removesuffix(".py")
        if m.endswith(".__init__"):
            m = m[: -len(".__init__")]
        return m

    def find_missing(self, shared_paths: Set[str]
                     ) -> List[Tuple[str, List[str]]]:
        shared_modules: Set[str] = set()
        for sp in shared_paths:
            m = self._to_module(sp)
            shared_modules.add(m)
            parts = m.split(".")
            for i in range(1, len(parts) + 1):
                shared_modules.add(".".join(parts[:i]))

        missing: List[Tuple[str, List[str]]] = []
        for module in sorted(self.all_modules):
            root = module.split(".")[0]
            if root not in INTERNAL_ROOTS:
                continue
            if module in shared_modules:
                continue
            importers: Set[str] = set(self.reverse.get(module, set()))
            for imp, users in self.reverse.items():
                if imp.startswith(module + "."):
                    importers.update(users)
            missing.append((module, sorted(importers)))
        return missing


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--shared", default="shared.txt")
    p.add_argument("--list-shared", action="store_true")
    p.add_argument("--output", default="text", choices=["text", "json"])
    args = p.parse_args()

    an = ImportAnalyzer(args.root)
    an.scan()

    if args.list_shared:
        for m in sorted(an.all_modules):
            if m.split(".")[0] in INTERNAL_ROOTS:
                print(m.replace(".", "/") + ".py")
        return

    shared: Set[str] = set()
    try:
        with open(args.shared, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    shared.add(line)
    except FileNotFoundError:
        print(f"error: {args.shared} not found", file=sys.stderr)
        sys.exit(1)

    missing = an.find_missing(shared)

    if args.output == "json":
        print(json.dumps(
            [{"module": m, "importers": importers} for m, importers in missing],
            ensure_ascii=False, indent=2,
        ))
        return

    print(f"=== {len(missing)} missing internal module(s) ===\n")
    for module, importers in missing:
        print(f"  {module}")
        if importers:
            print(f"    importers ({len(importers)}):")
            for imp in importers[:8]:
                print(f"      <- {imp}")
            if len(importers) > 8:
                print(f"      ... (+{len(importers) - 8})")
        print()


if __name__ == "__main__":
    main()