# sdk_doc_tools/class_index.py
"""StaTable SDK API仕様書作成用：クラス・メソッド索引生成

Usage:
    cd code
    python sdk_doc_tools/class_index.py

Outputs:
    sdk_doc_tools/class_index.md    (Markdown要約)
    sdk_doc_tools/class_index.json  (機械可読)
"""
import ast, json
from pathlib import Path

# 走査対象（tools/ は既存用途のため除外）
ROOTS = [
    "statable",
    "statable_gui",
    "statable_gui/libcntrl",
    "statable_gui/transition_editor_direct",
    "codegen",
]

OUT_DIR = Path(__file__).parent

def scan_file(fp: Path):
    try:
        tree = ast.parse(fp.read_text(encoding="utf-8"))
    except Exception as e:
        return {"_error": str(e)}
    classes = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = [
                n.name for n in node.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            classes.append({
                "class": node.name,
                "bases": [ast.unparse(b) for b in node.bases],
                "methods": methods,
                "lineno": node.lineno,
            })
    return classes

def main():
    result = {}
    for root in ROOTS:
        for fp in Path(root).rglob("*.py"):
            if "__pycache__" in str(fp):
                continue
            result[str(fp)] = scan_file(fp)

    (OUT_DIR / "class_index.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8")

    lines = ["# StaTable Class Index\n",
             f"Roots: {', '.join(ROOTS)}\n"]
    for fp, classes in sorted(result.items()):
        lines.append(f"## `{fp}`")
        if isinstance(classes, dict) and "_error" in classes:
            lines.append(f"- ⚠ parse error: {classes['_error']}")
            lines.append("")
            continue
        if not classes:
            lines.append("- (no classes)")
            lines.append("")
            continue
        for c in classes:
            lines.append(f"- **{c['class']}** (L{c['lineno']}) "
                         f"bases={c['bases']}")
            for m in c["methods"]:
                lines.append(f"    - `{m}`")
        lines.append("")

    (OUT_DIR / "class_index.md").write_text(
        "\n".join(lines), encoding="utf-8")
    print(f"Scanned {len(result)} files → "
          f"{OUT_DIR/'class_index.md'}")

if __name__ == "__main__":
    main()