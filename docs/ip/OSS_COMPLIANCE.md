# OSS License Compliance Statement

**Product**: StaTable v3.5.3
**Date**: 2026-10-11
**Author**: Hideki Akashi

## Summary

StaTable is fully compliant with all OSS licenses of its dependencies
and is safe for commercial distribution, including sale to third parties.

## Runtime Dependencies

### Core (`pip install statable`)

**Zero dependencies.** Confirmed by:

```
$ pip show statable
Requires:           # empty

$ pipdeptree --packages statable
statable==3.0.0     # no children
```

No third-party libraries are bundled with or required by StaTable core.

### GUI Extra (`pip install statable[gui]`)

**PySide6** - `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`
- Distributed under **LGPL-3.0** terms.
- **Dynamically linked** (DLL) -> no source disclosure obligation.
- License text included in the distribution.
- LGPL requirement met: users can replace PySide6 with a compatible version.

## Build Tools (not distributed)

**PyInstaller** - GPLv2 with **Bootloader Exception**.
- The exception explicitly permits distribution of proprietary
  applications built with PyInstaller.
- Reference: https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt

## Development Dependencies (not distributed)

`pytest`, `pycparser`, `mypy`, `coverage`, `tomli` - used only for
testing and development. Not shipped with the product.

## No GPL/AGPL Contamination

The following packages were detected in the developer's global
environment but are **NOT** dependencies of StaTable:

- PyMuPDF (AGPL-3.0)
- PyQt5 / PyQt6 (GPL-3.0)
- Unidecode (GPLv2+)
- Win32Security (GPLv3)
- django-autoslug (LGPL) - unrelated
- psycopg2-binary (LGPL) - unrelated
- opentimestamps (LGPLv3+) - installed for IP timestamping only

## Verification Commands

```
pip show statable           # Requires: empty
pip-licenses --packages statable
pipdeptree --packages statable
```

## Compliance Checklist

- [x] No GPL/AGPL in runtime dependencies
- [x] PySide6 (LGPL) dynamically linked
- [x] PySide6 license text included in distribution
- [x] PyInstaller Bootloader Exception documented
- [x] Dev dependencies excluded from distribution
- [x] License inventory stored in `docs/ip/`

## Conclusion

StaTable v3.5.3 can be commercially distributed and sold without
any OSS license restrictions on its own source code.