# Changelog

All notable changes to StaTable will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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