#!/usr/bin/env python3
"""Verify create_type_name() idempotency (v2.2.5)."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    from codegen.naming_convention import CNamingConvention

    cases = [
        # (input, expected)
        ("SystemStatus",     "SystemStatus_t"),
        ("SystemStatus_t",   "SystemStatus_t"),    # idempotent
        ("SensorData",       "SensorData_t"),
        ("SensorData_t",     "SensorData_t"),      # idempotent
        ("sensor_data",      "SensorData_t"),
        ("sensor_data_t",    "sensor_data_t"),     # preserved
        ("",                 "Unknown_t"),
        ("my_type",          "MyType_t"),
        ("my_type_t",        "my_type_t"),         # idempotent
    ]

    passed = 0
    failed = 0
    for inp, expected in cases:
        result = CNamingConvention.create_type_name(inp)
        ok = (result == expected)
        status = "[PASS]" if ok else "[FAIL]"
        print(f"  {status} create_type_name({inp!r}) -> {result!r} (expected {expected!r})")
        if ok:
            passed += 1
        else:
            failed += 1

    print()
    print(f"TOTAL: {passed + failed}  PASSED: {passed}  FAILED: {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())