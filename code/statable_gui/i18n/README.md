# StaTable GUI - Internationalization (i18n)

This directory holds translation resources for the StaTable GUI.

## Supported languages

| Code   | Language          | Status       |
|--------|-------------------|--------------|
| `en`   | English (default) | n/a (source) |
| `ja`   | Japanese          | planned      |
| `zh_CN`| Chinese (Simplified) | planned   |

## Files

- `statable_<lang>.ts` - Translation source (XML, human-editable)
- `statable_<lang>.qm` - Compiled translation (loaded by QTranslator)

## Workflow

### 1. Wrap translatable strings

In GUI code, wrap user-visible strings with `self.tr(...)`:

    self.setWindowTitle(self.tr("Code generation"))

### 2. Extract strings to .ts files

    cd code
    python tools/i18n_extract.py

This runs `lupdate` and regenerates `statable_ja.ts` and `statable_zh_CN.ts`.

### 3. Translate

Option A: Open with Qt Linguist

    "C:\Program Files\Python313\Lib\site-packages\PySide6\linguist.exe" statable_gui/i18n/statable_ja.ts

Option B: Edit the .ts XML directly

Option C: Machine-translate then review (see HANDOVER for i18n).

### 4. Compile to .qm

    cd code
    python tools/i18n_compile.py

This runs `lrelease` on every `*.ts` and produces `*.qm`.

### 5. Test

    cd code
    python -c "import sys; sys.path.insert(0, '.'); from statable_gui.i18n import install_translator; print('OK')"

Run the GUI and switch language via Settings menu.

## Adding a new language

1. Add the language code to `SUPPORTED_LANGUAGES` in `__init__.py`
2. Add display name to `LANG_DISPLAY`
3. Add the code to `LANGS` in `tools/i18n_extract.py`
4. Run extract + translate + compile
