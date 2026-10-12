# StaTable v3.5.3

**Release date:** 2026-10-11
**PyPI:** https://pypi.org/project/statable/3.5.3/

## Highlights

### Eclipse Installer v0.1.1 (separate standalone release)

- core.py: remove duplicate .settings/* write.
  Each file was written once but appeared in both installed and
  skipped (cosmetic; file system unaffected).
- Templates: normalize encoding
  - Remove UTF-8 BOM (main_demo.c, startup_stm32f405.s, syscalls.c)
  - Convert CRLF -> LF across all templates
- Add README.md (EN) / README_zh.md (ZH)

### Deep test suite

- test_v3_5_3_eclipse_installer_deep.py (80 PASS):
  L1 template integrity + L2 core.install edge cases.
- tools/e2e_eclipse_installer.py (local-only):
  L3 compile, L4 link, L5 QEMU UART banner.

## Verification

- 49 test suites / **1873 PASS** / 0 FAIL
- mypy: 0 errors in 118 files
- Eclipse Installer CLI: Installed: 67, Skipped: 0, Errors: 0
- E2E (local): firmware.bin 5192 bytes + UART banner

## Related releases

- eclipse-installer-v0.1.1: standalone installer ZIP (45.8 MB)
- v3.5.2: Phase 1c mypy cleanup
- v3.5.1: Eclipse Installer added to repository
- v3.5.0: S-GUI + Portable ZIP

## Installation (PyPI)

    pip install statable==3.5.3

## Remaining (v3.5.4+)

- S-3 Step 2: ubuntu-26.04 preview job (2026-10-19 onwards)
