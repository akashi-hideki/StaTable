# StaTable

**MISRA C:2012-aware state machine design and C code generation for embedded systems.**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/akashi-hideki/StaTable/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-1479%20PASS-green.svg)](https://github.com/akashi-hideki/StaTable)
[![MISRA](https://img.shields.io/badge/MISRA-C%3A2012-orange.svg)](https://www.misra.org.uk/)

StaTable is a Python-based tool for designing state machines and
generating **MISRA C:2012-compliant C code** for embedded systems.
It provides a CLI, a Python SDK, and a PySide6 GUI.

---

## Features

- **MISRA C:2012-aware C code generation** — validated with `cppcheck` + official MISRA addon
- **Multi-layer state machines** — Driver / Middleware / Application with priority execution
- **State actions (Entry / Exit / Do)** — table-driven dispatch with user-code markers
- **35 validation rules** across 11 categories with AI-assisted diagnostics
- **Marker-based user code preservation** — regenerate without losing your custom code
- **CLI + SDK + GUI** — integrate into any workflow
- **Pure Python** — easy to install and extend
- **i18n**: English and Simplified Chinese (简体中文)

---

## Installation

**SDK + CLI only:**

```
pip install statable
```

**With GUI (PySide6):**

```
pip install "statable[gui]"
```

**Development:**

```
pip install "statable[dev]"
```

---

## Quick Start

### CLI

```
statable-cli version
statable-cli generate --xml design.xml --out generated/ --format json
statable-cli validate --xml design.xml --format json --exit-on-error
```

### Python SDK

```
from statable import State, Event, Transition, StateMachine, StateType, EventKind
from statable.global_defs import GlobalDefinitions
from codegen import CCodeGenerator, CodeGenerationConfig

sm = StateMachine()
sm.add_state(State(name="Idle", type=StateType.INITIAL))
sm.add_state(State(name="Running"))
sm.add_event(Event(name="START", kind=EventKind.SIGNAL))
sm.set_initial("Idle")
sm.add_transition(Transition(source="Idle", event="START", target="Running"))

cfg = CodeGenerationConfig()
gen = CCodeGenerator(config=cfg)
files = gen.generate_all_layers([("Application", sm)], GlobalDefinitions())
gen.save_generated_code(files, "generated/")
```

### GUI

```
python -m statable
```

Menu: **Language / 语言** → switch between **English** and **简体中文**.

---

## Requirements

- Python 3.10 or later
- PySide6 >= 6.0 (for GUI)
- pycparser (optional, for advanced parsing)

---

## Links

- **Homepage**: https://github.com/akashi-hideki/StaTable
- **Documentation**: https://github.com/akashi-hideki/StaTable/blob/main/README.md
- **Issues**: https://github.com/akashi-hideki/StaTable/issues
- **Chinese README**: https://github.com/akashi-hideki/StaTable/blob/main/README_zh-CN.md

---

## License

Apache License 2.0 — free for commercial and personal use.

See [LICENSE](https://github.com/akashi-hideki/StaTable/blob/main/LICENSE) for details.

---

## Acknowledgments

- [PySide6](https://www.qt.io/qt-for-python) — Qt 6 for Python
- [cppcheck](https://cppcheck.sourceforge.io/) — static analysis
- All contributors and users

---

If StaTable helps you, please consider giving it a ⭐ on GitHub.
