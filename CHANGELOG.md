# Changelog

All notable changes to StaTable will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.2.0] - 2026-10-03

### Added

- **New Project Wizard** — 4-page wizard accessible from
  `File -> New Project...` (Ctrl+N):
  1. Project info (name, output folder)
  2. Template selection (3 templates)
  3. Customize names (rename States / Role Functions / Events /
     Interrupts / Variables / Flags / Queues)
  4. Preview before generation
- **3 project templates**:
  - `3-Layer (Driver / Middleware / Application) [Recommended]`
  - `Basic (Single Layer)`
  - `Empty Project`
- **Placeholder generation per layer** (5 states / 5 events /
  5 role functions) and globally (5 interrupts / 5 variables /
  5 flags / 5 event queues).
- **+58 unit tests** in `tests/test_v3_2_s1_wizard.py` covering
  templates, generation, rename, and file menu.

### Changed

- **File menu simplified** — single `New Project...` entry
  (previously `New Project (Empty)...` + `New Project (Wizard)...`).
- **Complete Chinese i18n for the New Project Wizard** —
  all page titles, labels, buttons, table headers, category values,
  template names, and template descriptions translated to
  Simplified Chinese.
- **README** — added "What's New in v3.2.0" section and
  "v3.2.0" roadmap entry; updated test count to 1537.
- **Test suite** — updated version expectations to 3.2.0 in
  `test_v3_0_s1_packaging.py`, `test_v3_0_s2_public_api.py`,
  `test_v3_0_s3_cli.py`.

### Fixed

- (none)

## [3.1.1] - 2026-10-03

### Changed

- **README updated for PyPI release** - added PyPI badges,
  `pip install statable` instructions, CLI usage section, and
  updated roadmap to reflect v3.0 / v3.1.0 as released.
- **License declaration migrated to SPDX format** in `pyproject.toml`
  (`license = "Apache-2.0"` instead of TOML table). The deprecated
  `License :: OSI Approved :: Apache Software License` classifier
  has been removed. This aligns with [PEP 639](https://peps.python.org/pep-0639/)
  and avoids the setuptools deprecation warning (deadline: 2027-02-18).
- **.gitignore hardened** - block `github-recovery*.txt` patterns
  to prevent accidental commit of GitHub 2FA recovery codes.

### Fixed

- (none)

## [3.1.0] - 2026-10-03

### Added

- **PyPI release** - `pip install statable` is now available at
  https://pypi.org/project/statable/
- **GitHub Release v3.1.0** with wheel + sdist attached.
- **CLI** - `statable-cli generate / validate / version`
- **Python API** - `import statable` with 21 public symbols.

### Chinese Language Support

- **Simplified Chinese GUI** - 97.4% translated (485 / 498 strings).
- **Language menu** - switch between English and Chinese.
- **Auto restart** on language change.

## [3.0.0] - 2026-10-02

### Added

- SDK foundation: CLI, Python SDK, Apache-2.0 license with
  commercial / OEM options.

[3.1.1]: https://github.com/akashi-hideki/StaTable/releases/tag/v3.1.1
[3.1.0]: https://github.com/akashi-hideki/StaTable/releases/tag/v3.1.0
[3.0.0]: https://github.com/akashi-hideki/StaTable/releases/tag/v3.0