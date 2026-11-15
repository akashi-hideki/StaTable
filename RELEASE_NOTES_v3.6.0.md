# StaTable v3.6.0 — Communication Monitor

**Release date:** 2026-11-15
**PyPI:** https://pypi.org/project/statable/3.6.0/

## Components

| Component | Version | Asset |
|---|---|---|
| StaTable core / GUI | 3.6.0 | `statable-3.6.0-py3-none-any.whl`, `statable-3.6.0.tar.gz` |
| StaTable Monitor GUI | 3.6.0 | `StaTableMonitorGUI-v3.6.0-win64.zip` |
| Eclipse Installer | 0.1.2 | `StaTable-Eclipse-Installer-v0.1.2-win64.zip` |

## Highlights

### Communication Monitor (core)

- Global variable monitor over UART (ASCII mode): PING / LIST / GET / HELP.
- Generated: `statable_comm_monitor.c/h`, `statable_comm_config.h`,
  `statable_comm_registry.c/h`, `statable_comm_ring.c/h`.
- Spec: `code/docs/SPEC_COMM_MONITOR_v1_2.md`.

### StaTable Monitor GUI

- PC-side reference GUI (`python -m statable_monitor_gui`)
- Simulator mode (triangle wave) + real COM (pyserial enumeration)
- psblog/v1 logging, PowerSimBuilder integration
- Standalone EXE (~47 MB onefile)

### Python SDK — statable_monitor

- `StaTableMonitor` with `connect() / ping() / list_variables() / get() / get_many()`
- `create_logger()` (psblog/v1 writer)

### Eclipse Installer v0.1.2

- Fix: "progress dialog appears stuck" on frozen EXE
- Async QThread install + startup preload + output directory guard

## Verification

- (Phase 3 のテスト結果を反映)

## Known limitations (v3.6.1 candidates)

- `statable_comm_commands.c` (user-extensible command table) not yet generated.
- `COMM_MONITOR_IDLE_MS` (idle timeout) declared but not wired.

## Related releases

- eclipse-installer-v0.1.2: standalone installer ZIP (~46 MB)
- v3.5.3: Eclipse Installer v0.1.1 + mypy 0 errors
- v3.5.0: GUI output-directory hygiene

## Installation (PyPI)

    pip install statable==3.6.0
