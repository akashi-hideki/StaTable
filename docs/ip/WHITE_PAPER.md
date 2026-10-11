# StaTable Technical White Paper

**Version**: 1.0
**Date**: 2026-10-11
**Author**: Hideki Akashi
**Status**: Confidential — For Evaluation Purposes Only

---

## 1. Executive Summary

StaTable is a MISRA C:2012-aware state machine design and C code
generation tool for embedded systems. It enables embedded engineers
to design complex state machines visually and generate production-ready,
MISRA-compliant C99 code automatically.

**Key Value Propositions:**
- **Zero-dependency core** — no third-party runtime libraries
- **MISRA C:2012 compliant** — validated by cppcheck with official addon
- **Eclipse integration** — ready for existing toolchains
- **QEMU-verified** — ARM Cortex-M4 real-machine link proven
- **Multi-language** — 日本語 / English / 简体中文
- **Apache-2.0 licensed** — commercially usable

**Target Market:** Embedded engineers and appliance manufacturers in
China and Japan, particularly in automotive, medical, and industrial
equipment sectors.

**Current Status:** v3.5.3 released (2026-10-11) on PyPI and GitHub.
- 49 test suites / 1873 PASS / 0 FAIL
- mypy: 0 errors in 118 files
- ARM Cortex-M4 link verification: PASS

---

## 2. Technical Overview

### 2.1 Architecture

StaTable employs a seven-layer state machine architecture:

1. **Application** — top-level system logic
2. **MwMicrowave** — microwave control middleware
3. **MwOven** — oven control middleware
4. **MwGrill** — grill control middleware
5. **MwSteam** — steam control middleware
6. **DriverInput** — sensor / RX / door safety inputs
7. **DriverOutput** — heater / fan / TX outputs

The layered design allows independent development and testing of
each subsystem, with clear interfaces between layers.

### 2.2 Code Generation

StaTable generates C99 code from a state × event matrix:

- **Table-driven dispatch** — optimized for embedded MCUs
- **State actions** — UML Entry / Exit / Do semantics
- **User code preservation** — marker-based merger protects
  hand-written code across regenerations
- **File-level markers** — `[[STABLE_USER_CODE_START]]` /
  `[[STABLE_USER_CODE_END]]` blocks for file-scope user code

### 2.3 Validation

- **35 validation rules** across 11 categories
- **MISRA C:2012 compliance** — cppcheck with official MISRA addon
- **ARM Cortex-M4 link verification** — proven on real hardware
- **QEMU execution** — netduinoplus2 emulation for CI

### 2.4 Interfaces

- **GUI** — PySide6-based, Chinese/English/Japanese UI
- **CLI** — `statable-cli generate` / `validate`
- **Python SDK** — 21 public symbols for programmatic use
- **Eclipse Installer** — standalone tool for Eclipse 4.41 integration

---

## 3. Market Background

### 3.1 Global Embedded Tools Market

- 2025 market size: ~USD 5.9 billion
- Projected 2030: ~USD 10.4 billion (CAGR 12%)
- Drivers: MISRA C:2025 updates, UNECE R155/R156 cybersecurity,
  shift from in-house to commercial toolchains

### 3.2 China Market

- Growth rate: 1.5× global average
- Key sectors: automotive, medical, industrial, home appliances
- Demand: MISRA C compliance, local-language documentation,
  Eclipse integration

### 3.3 Regulatory Drivers

- **MISRA C:2025** — updated compliance requirements
- **UNECE R155/R156** — automotive cybersecurity
- **China GB standards** — local functional safety requirements

---

## 4. Technical Advantages

| Feature | StaTable | Typical Competitor |
|---------|----------|-------------------|
| Runtime dependencies | Zero | Multiple |
| MISRA C:2012 | Native | Add-on |
| User code preservation | Marker-based | Manual |
| Eclipse integration | Native installer | Manual setup |
| QEMU verification | Built-in | None |
| Multi-language UI | 3 languages | 1-2 languages |
| License | Apache-2.0 | Proprietary |

### 4.1 Quality Metrics

- **49 test suites / 1873 PASS / 0 FAIL**
- **mypy: 0 errors in 118 files**
- **CI: 11 jobs green** (including ARM link, gcc strict, MISRA)
- **Eclipse Installer CLI**: 67 installed, 0 errors

### 4.2 Development Velocity

- v3.0 → v3.5.3 in 9 days (with 49 suites added)
- Demonstrates rapid iteration capability

---

## 5. Intellectual Property

### 5.1 Development Timeline Proof

All major release tags (v3.3.0 through v3.5.3) have been timestamped
using RFC 3161 (FreeTSA). This provides legally-verifiable proof of
existence at specific points in time.

**Location:** Repository root, `*.tsr` files
**Verification:** `openssl ts -verify` — all return `Verification: OK`

### 5.2 OSS License Compliance

**Core runtime dependencies: ZERO.**

Verified by:
```
$ pip show statable
Requires:           # empty
```

**GUI extra (PySide6):** LGPL-3.0, dynamically linked.
No source disclosure obligation for StaTable code.

**No GPL/AGPL contamination in runtime dependencies.**

Full statement: `docs/ip/OSS_COMPLIANCE.md`

### 5.3 Copyright

- **Author**: Hideki Akashi
- **License**: Apache-2.0 (allows commercial use, modification,
  distribution, and sublicensing)
- **Repository**: https://github.com/akashi-hideki/StaTable

### 5.4 Potential Patent Areas

The following areas may warrant patent consideration:
- Table-driven state machine dispatch with layered architecture
- Marker-based user code preservation across regenerations
- MISRA-aware code generation with rule suppression optimization

*Consultation with patent attorney recommended before any disclosure.*

---

## 6. China Market Fit

### 6.1 Localization

- **Chinese UI** — 97.4% translated (485/498 strings)
- **Chinese documentation** — TUTORIAL_zh.md (57.2 KB),
  USER_CODE_GUIDE_zh.md (11.7 KB)
- **Chinese README** — README_zh.md
- **Eclipse Installer** — Chinese README included

### 6.2 Integration

- **Eclipse 4.41 ARM Cross GCC** — fully tested
- **QEMU netduinoplus2** — verified on emulator
- **STM32 support** — G4 recommended, G0/F4/F7 tested
- **GD32 compatible** — domestic Chinese MCU alternative

### 6.3 Distribution

- **PyPI** — `pip install statable`
- **GitHub Releases** — Portable ZIP (174 MB, no Python required)
- **Gitee mirror** — in progress (awaiting support response)

---

## 7. Business Model Options

### 7.1 Acquisition

Full transfer of all IP rights, source code, and documentation.
Buyer would gain:
- Complete StaTable codebase (Apache-2.0 licensed)
- All documentation (3 languages)
- Eclipse Installer
- Development history with timestamps

### 7.2 Licensing

- **OEM License** — embed StaTable in commercial products
- **Enterprise License** — site-wide deployment
- **Custom Development** — bespoke features for specific needs

### 7.3 Joint Venture

- Co-development of China-specific features
- Joint marketing in Chinese market
- Revenue sharing model

---

## 8. Roadmap

### 8.1 Short-term (v3.6-v3.7)

- ubuntu-26.04 CI preview (2026-10-19 onwards)
- Enhanced Chinese documentation
- Additional MCU support (STM32H7, etc.)

### 8.2 Medium-term (v4.0)

- Cloud-based code generation
- AI-assisted state machine design
- Expanded appliance templates

### 8.3 Long-term

- Integration with mainstream Chinese IDEs
- Certification support (IEC 61508, ISO 26262)
- Multi-vendor MCU support

---

## 9. Contact

**Author**: Hideki Akashi
**Repository**: https://github.com/akashi-hideki/StaTable
**Email**: (available upon request)
**Location**: Japan

---

*This document is confidential and provided for evaluation purposes
only. No license or rights are granted by its disclosure.*