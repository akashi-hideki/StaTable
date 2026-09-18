"""StaTable preference definitions (key names and default values)\n\nTo add or change a setting, just add/edit an entry in\nPREFERENCE_DEFINITIONS in this file.\n"""

from pathlib import Path

# ----------------------------------------------------------------------
#Setting item definitions
# Adding an entry here is enough to enable attribute access from the Preferences class.
# ----------------------------------------------------------------------
PREFERENCE_DEFINITIONS = {
    # Last used folder
    "last_project_dir": str(Path.home()),       # Project XML
    "last_c_source_dir": str(Path.home()),      # C source output dir
    "last_spec_doc_dir": str(Path.home()),      # Spec documents location
    "last_export_dir": str(Path.home()),        # Export dir

    # ★ Event delivery settings
    "auto_convert_isr_direct_to_double": True,  # Automatically convert ISR-used DIRECT to DOUBLE
}