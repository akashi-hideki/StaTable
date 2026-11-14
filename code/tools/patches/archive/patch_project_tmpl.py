"""patch_project_tmpl.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "eclipse_installer" / "templates" / "project.tmpl"

content = """<?xml version="1.0" encoding="UTF-8"?>
<projectDescription>
\t<name>@@PROJECT_NAME@@</name>
\t<comment></comment>
\t<projects>
\t</projects>
\t<buildSpec>
\t\t<buildCommand>
\t\t\t<name>org.eclipse.cdt.managedbuilder.core.genmakebuilder</name>
\t\t\t<triggers>clean,full,incremental,</triggers>
\t\t\t<arguments>
\t\t\t</arguments>
\t\t</buildCommand>
\t\t<buildCommand>
\t\t\t<name>org.eclipse.cdt.managedbuilder.core.ScannerConfigBuilder</name>
\t\t\t<triggers>full,incremental,</triggers>
\t\t\t<arguments>
\t\t\t</arguments>
\t\t</buildCommand>
\t</buildSpec>
\t<natures>
\t\t<nature>org.eclipse.cdt.core.cnature</nature>
\t\t<nature>org.eclipse.cdt.managedbuilder.core.managedBuildNature</nature>
\t\t<nature>org.eclipse.cdt.managedbuilder.core.ScannerConfigNature</nature>
\t</natures>
</projectDescription>
"""
P.write_text(content, encoding="utf-8")
print(f"[OK] {P}")
print(f"[INFO] tab bytes: {P.read_bytes().count(9)}")
