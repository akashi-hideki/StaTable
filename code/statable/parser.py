# statable/parser.py
"""
StaTable parser (unimplemented stub)

[v1.8 section 11.2 #9]
  Currently an unimplemented stub.
  XML I/O is handled by `statable/xml_io.py`.

[Planned for future implementation]
  - Excel (.xlsx) loading
    Import state transition tables using openpyxl etc.
  - CSV (.csv) loading
    Assume state x event matrix format
  - JSON (.json) loading
    General-purpose format for external tool integration

[Notes]
  - This module currently has no callers
  - When implementing, convert to `statable/model.py`'s
    StateMachine / State / Event / Transition
  - It is desirable to target the same interface as the existing `xml_io.py`
    (equivalent to project_to_xml / project_from_xml)

[If not implementing]
  This file itself can be deleted without issue.
  Since there are no callers, deletion has no impact.
"""

# ======================================================================
# Unimplemented marker
# ======================================================================
# The following are placeholders.
# Do not call until implemented.

__all__ = []   # No public API (not implemented)


class ParserNotImplementedError(NotImplementedError):
    """Exception indicating parser.py features not implemented"""
    pass


def parse_excel(filepath: str):
    """\n    Load state transition data from an Excel file (not implemented)\n"""
    raise ParserNotImplementedError(
        "parse_excel is not implemented."
        "Currently, please use statable/xml_io.py."
    )


def parse_csv(filepath: str):
    """\n    Load state transition data from a CSV file (not implemented)\n"""
    raise ParserNotImplementedError(
        "parse_csv is not implemented."
        "Currently, please use statable/xml_io.py."
    )


def parse_json(filepath: str):
    """\n    Load state transition data from a JSON file (not implemented)\n"""
    raise ParserNotImplementedError(
        "parse_json is not implemented."
        "Currently, please use statable/xml_io.py."
    )