# L1 host test

Generated C code is built with gcc and driven via stdin/stdout.

Files:

- test_main.c     : stdin -> comm_monitor -> stdout
- fake_registry.c : 5 fake variables

Run tests:

    pytest tests/test_v3_6_0_comm_monitor_ascii.py -v

Requirements:

- gcc on PATH (MinGW, MSYS2, or WSL)
