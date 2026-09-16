#!/usr/bin/env python3
"""StaTable 一貫性チェック - コアロジック（GUI 非依存）"""
from __future__ import annotations

import ast
import difflib
import importlib
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional


@dataclass
class CheckResult:
    name: str
    status: str = "SKIP"          # PASS / FAIL / SKIP / ERROR
    summary: str = ""
    details: List[str] = field(default_factory=list)
    table_headers: List[str] = field(default_factory=list)
    table_rows: List[List[str]] = field(default_factory=list)


def _read(path) -> str:
    return Path(path).read_text(encoding="utf-8")


def _iter_py(dirs):
    for d in dirs:
        p = Path(d)
        if p.is_file() and p.suffix == ".py":
            yield p
        elif p.is_dir():
            yield from p.rglob("*.py")


def _normalize_xml(text: str) -> str:
    try:
        return ET.canonicalize(text, strip_text=True)
    except Exception:
        root = ET.fromstring(text)
        return ET.tostring(root, encoding="unicode")


def _diff(a: str, b: str, name_a="original", name_b="roundtrip") -> str:
    return "\n".join(difflib.unified_diff(
        a.splitlines(), b.splitlines(),
        fromfile=name_a, tofile=name_b, lineterm="",
    ))


def _find_func(mod, names):
    for n in names:
        if hasattr(mod, n):
            return getattr(mod, n)
    return None


class ConsistencyChecker:
    """一貫性チェック本体。各 check_* メソッドが CheckResult を返す。"""

    LOAD_NAMES = ["load", "load_from_file", "load_state_machine", "read_xml", "read"]
    SAVE_NAMES = ["save", "save_to_file", "save_state_machine", "write_xml", "write"]

    def __init__(self, root: Path, xml_path: Path, xml_io_path: Path,
                 model_path: Path, scan_dirs: List[Path], output_dir: Path,
                 logger: Optional[Callable[[str], None]] = None):
        self.root = Path(root).resolve()
        self.xml_path = Path(xml_path)
        self.xml_io_path = Path(xml_io_path)
        self.model_path = Path(model_path)
        self.scan_dirs = [Path(d) for d in scan_dirs]
        self.output_dir = Path(output_dir)
        self._log = logger or (lambda msg: None)

    # ---------- 1. XML round-trip ----------
    def check_roundtrip_xml(self) -> CheckResult:
        r = CheckResult(name="XML round-trip")
        if not self.xml_path.exists():
            r.status = "SKIP"
            r.summary = f"XML not found: {self.xml_path}"
            return r
        try:
            if str(self.root) not in sys.path:
                sys.path.insert(0, str(self.root))
            rel = self.xml_io_path.resolve().relative_to(self.root)
            mod = importlib.import_module(".".join(rel.with_suffix("").parts))
        except Exception as e:
            r.status = "ERROR"
            r.summary = f"import failed: {e}"
            return r

        load = _find_func(mod, self.LOAD_NAMES)
        save = _find_func(mod, self.SAVE_NAMES)
        if not load or not save:
            r.status = "ERROR"
            r.summary = "load/save function not found in xml_io"
            return r

        tmp = None
        try:
            self._log(f"Loading {self.xml_path}...")
            obj = load(str(self.xml_path))
            with tempfile.NamedTemporaryFile("w", suffix=".xml",
                                             delete=False, encoding="utf-8") as f:
                tmp = f.name
            try:
                save(obj, tmp)
            except TypeError:
                save(tmp, obj)
            orig = _normalize_xml(self.xml_path.read_text(encoding="utf-8"))
            new = _normalize_xml(Path(tmp).read_text(encoding="utf-8"))
            if orig == new:
                r.status = "PASS"
                r.summary = "正規化後、完全一致"
            else:
                r.status = "FAIL"
                r.summary = "round-trip 差分あり"
                r.details.append(_diff(orig, new))
        except Exception as e:
            r.status = "ERROR"
            r.summary = f"exception: {e}"
        finally:
            if tmp:
                Path(tmp).unlink(missing_ok=True)
        return r

    # ---------- 2. フィールドマトリクス ----------
    def check_fields(self) -> CheckResult:
        r = CheckResult(name="Fields matrix")
        if not self.model_path.exists():
            r.status = "SKIP"
            r.summary = f"model not found: {self.model_path}"
            return r
        try:
            tree = ast.parse(_read(self.model_path))
        except Exception as e:
            r.status = "ERROR"
            r.summary = f"parse failed: {e}"
            return r

        target_classes = ["Transition", "RoleFunction"]
        fields: Dict[str, List[str]] = {}
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name in target_classes:
                fs = []
                for stmt in node.body:
                    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                        fs.append(stmt.target.id)
                fields[node.name] = fs

        if not fields:
            r.status = "SKIP"
            r.summary = "対象クラス未検出"
            return r

        matrix: Dict[str, Dict[str, List[str]]] = {
            cls: {f: [] for f in fs} for cls, fs in fields.items()
        }
        for p in _iter_py(self.scan_dirs):
            try:
                text = _read(p)
            except Exception:
                continue
            rel = str(p.relative_to(self.root))
            for cls, fs in fields.items():
                for f in fs:
                    pats = [rf"\.{f}\b", rf"\b{f}\s*=", rf"['\"]{f}['\"]", rf"\b{f}\s*:"]
                    if any(re.search(pat, text) for pat in pats):
                        matrix[cls][f].append(rel)

        r.table_headers = ["class", "field", "referenced in"]
        for cls, fs in fields.items():
            for f in fs:
                refs = matrix[cls][f]
                r.table_rows.append([cls, f, ", ".join(refs) if refs else "(none)"])
        n_missing = sum(1 for row in r.table_rows if row[2] == "(none)")
        r.status = "PASS" if n_missing == 0 else "FAIL"
        r.summary = f"{len(fields)} クラス / {sum(len(v) for v in fields.values())} フィールド / 未参照 {n_missing}"
        return r

    # ---------- 3. Enum 使用箇所 ----------
    def check_enums(self) -> CheckResult:
        r = CheckResult(name="Enum usage")
        if not self.model_path.exists():
            r.status = "SKIP"
            r.summary = f"model not found: {self.model_path}"
            return r
        try:
            tree = ast.parse(_read(self.model_path))
        except Exception as e:
            r.status = "ERROR"
            r.summary = f"parse failed: {e}"
            return r

        enums: Dict[str, List[str]] = {}
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
                if "Enum" in bases or "IntEnum" in bases:
                    members = []
                    for stmt in node.body:
                        if isinstance(stmt, ast.Assign):
                            for t in stmt.targets:
                                if isinstance(t, ast.Name):
                                    members.append(t.id)
                        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                            members.append(stmt.target.id)
                    enums[node.name] = members

        if not enums:
            r.status = "SKIP"
            r.summary = "Enum 未検出"
            return r

        usage: Dict[str, Dict[str, List[str]]] = {
            e: {m: [] for m in ms} for e, ms in enums.items()
        }
        for p in _iter_py(self.scan_dirs):
            try:
                text = _read(p)
            except Exception:
                continue
            rel = str(p.relative_to(self.root))
            for e, members in enums.items():
                for m in members:
                    if re.search(rf"\b{e}\.{m}\b", text):
                        usage[e][m].append(rel)

        r.table_headers = ["enum", "member", "referenced in"]
        n_missing = 0
        for e, members in enums.items():
            for m in members:
                refs = usage[e][m]
                if not refs:
                    n_missing += 1
                r.table_rows.append([e, m, ", ".join(refs) if refs else "(none)"])
        r.status = "PASS" if n_missing == 0 else "FAIL"
        r.summary = f"{len(enums)} Enum / {sum(len(v) for v in enums.values())} メンバー / 未参照 {n_missing}"
        return r

    # ---------- 4. 生成 C コード整合性 ----------
    def check_generated_c(self) -> CheckResult:
        r = CheckResult(name="Generated C")
        out = self.output_dir
        if not out.exists():
            r.status = "SKIP"
            r.summary = f"output not found: {out}"
            return r

        issues: List[str] = []
        for h in out.rglob("*.h"):
            text = h.read_text(encoding="utf-8", errors="ignore")
            if "#ifndef" not in text or "#define" not in text:
                issues.append(f"{h.relative_to(self.root)}: include guard なし")

        for h in out.rglob("statable_types_*.h"):
            if h.name == "statable_types_common.h":
                continue
            text = h.read_text(encoding="utf-8", errors="ignore")
            if "statable_types_common.h" not in text:
                issues.append(f"{h.relative_to(self.root)}: common.h 未 include")

        for layer_dir in out.iterdir():
            if not layer_dir.is_dir():
                continue
            header = layer_dir / f"statable_role_functions_{layer_dir.name}.h"
            source = layer_dir / f"statable_role_functions_{layer_dir.name}.c"
            if not header.exists() or not source.exists():
                continue
            h_text = header.read_text(encoding="utf-8", errors="ignore")
            c_text = source.read_text(encoding="utf-8", errors="ignore")
            protos = set(re.findall(r"\b(RoleFunc_\w+)\s*\(", h_text))
            defs = set(re.findall(r"\b(RoleFunc_\w+)\s*\(", c_text))
            missing = protos - defs
            if missing:
                issues.append(f"{layer_dir.name}: 定義なしプロトタイプ {sorted(missing)}")

        r.status = "PASS" if not issues else "FAIL"
        r.summary = f"検出 {len(issues)} 件"
        r.details = issues
        return r

    # ---------- 全実行 ----------
    def all_checks(self):
        return [
            ("XML round-trip", self.check_roundtrip_xml),
            ("Fields matrix", self.check_fields),
            ("Enum usage", self.check_enums),
            ("Generated C", self.check_generated_c),
        ]