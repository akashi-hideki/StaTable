!# 項目 2 → 6 → 5 順次実施 + 仕様書詳細版

---

# 項目 2: 仕様書 §1.3（動作環境）の修正

## 2.1 変更内容

| 項目 | 変更前 | 変更後 |
|---|---|---|
| Python 要件 | 3.9 以上 | **3.10 以上** |
| 推奨 | 3.12+ 推奨 | 3.12+ 推奨（変更なし） |

**理由**: `@dataclass(kw_only=True)` は Python 3.10 で導入。3.9 では `TypeError`。

## 2.2 仕様書 完全テキスト（§1.3 差替え）

```markdown
### 1.3 動作環境

| 項目 | 要件 |
|---|---|
| Python | **3.10 以上**（**3.12+ 推奨** — PEP 701 対応） |
| PySide6 | 6.x（QtWebEngine 含む） |
| OS | Windows / macOS / Linux |
| 生成コード | C99 以上 |

---

#### 1.3.1 Python 3.10 以上が必要な理由

StaTable v2.2 のデータモデルは `@dataclass(kw_only=True)` を使用しています。

| クラス | `kw_only` 導入版 | 定義箇所 |
|---|---|---|
| `RoleFunction` | v1.5 | `statable/model.py` |
| `Transition` | v1.6 | `statable/model.py` |
| `ActionStep` | v2.2 | `statable/model.py` |
| `TransitionRelation` | v2.2 | `statable/model.py` |

`@dataclass(kw_only=True)` は **Python 3.10** で導入された言語機能です。

- **Python 3.9 以前**: `TypeError: dataclass() got an unexpected keyword argument 'kw_only'`
- **Python 3.10 以上**: 正常動作

**設計意図**:

`kw_only=True` は、v1.5 / v1.6 で発生した **位置引数のフィールド順序事故** を構造的に防止します。

```python
# 旧（危険）: 引数順序を間違えても型エラーにならない
Transition("Idle", "START", "", ["init()"], "Active")

# 新（安全）: フィールド名を強制
Transition(source="Idle", event="START",
           condition="", pre_actions=["init()"], target="Active")
```

この安全性を **全 dataclass に一貫適用** しているため、Python 3.10+ が必須です。

---

#### 1.3.2 Python 3.12+ を推奨する理由（PEP 701）

**PEP 701**（f-string の拡張）により、Python 3.12 以降では f-string が以下の **3 種類のトークンに分割** されます。

| Python バージョン | `f"動作: {x}"` のトークン |
|---|---|
| 3.11 以前 | 1 個の `STRING` トークン |
| **3.12 以降** | `FSTRING_START('f"')` + `FSTRING_MIDDLE('動作: ')` + `FSTRING_MIDDLE('{x}')` + `FSTRING_END('"')` |

**影響**: `tokenize.STRING` のみを対象とする抽出ツール（`tools/extract_strings.py` / `tools/apply_translations.py`）は **f-string 内の日本語を見落とします**。

**対策**: StaTable v2.1 では以下を実施済みです。

- 抽出・検証には **生テキスト走査**（`tools/find_all_japanese.py`）を併用
- f-string 内の置換は単純な文字列置換で実施（`tools/apply_batch11_fstrings.py`）

両バージョンで検証可能ですが、**3.12+ の方が将来の拡張に適しています**。

---

#### 1.3.3 検証済み環境

| 項目 | 値 |
|---|---|
| **開発環境** | Python **3.13** |
| PySide6 | 6.x |
| OS | Windows 10 |
| テスト総数 | 457 |
| 生成 C ファイル | 24（3 層構成） |
| 生成コード検証 | errors=0, warnings=0 |

**本番環境推奨**: Python 3.10 以上（3.12+ が理想）
```

## 2.3 関連セクションへの波及

| セクション | 修正 |
|---|---|
| §1.3 | 上記 |
| §10.5 既知の制約 | 「Python 3.9 以上」前提の記述があれば「3.10 以上」に統一 |
| §11 バージョン履歴 | v2.2.5 行を追加（下記） |

### §11 バージョン履歴への追加行

```markdown
| **v2.2.5** | **Python 3.10+ 要件明記 / Custom type `_t` 二重化回避 / CI 組み込み** | 15 |
```

---

# 項目 6: CI 組み込み（日本語 + 生成コード検証）

## 6.1 仕様書 §14.4（CI 組み込み例）完全版

```markdown
### 14.4 CI 組み込み（完全版）

StaTable v2.2 は以下 4 つの CI ジョブを **GitHub Actions** で実行することを推奨します。

| # | ジョブ | 検証内容 | 失敗条件 |
|---|---|---|---|
| 1 | `no-japanese` | ソース・生成コード内の日本語残存 | 1 行でも検出 |
| 2 | `syntax` | Python 構文エラー | `compileall` 失敗 |
| 3 | `tests` | 全ユニットテスト（457 件） | 1 件でも FAIL |
| 4 | `generated-code` | 生成 C コードの構造検証 | errors > 0 |

---

#### 14.4.1 `.github/workflows/check.yml`（完全版）

```yaml
name: Check

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  workflow_dispatch:

jobs:
  # ==============================================================
  # Job 1: No Japanese characters in source / generated code
  # ==============================================================
  no-japanese:
    name: No Japanese characters
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Run find_all_japanese.py
        run: |
          python tools/find_all_japanese.py
          # Expect: "Total: 0 line(s) with Japanese"

  # ==============================================================
  # Job 2: Python syntax check
  # ==============================================================
  syntax:
    name: Python syntax check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install PySide6 (for import resolution)
        run: pip install PySide6

      - name: compileall
        run: |
          python -m compileall -q statable statable_gui codegen

  # ==============================================================
  # Job 3: Unit tests (457 tests)
  # ==============================================================
  tests:
    name: Unit tests
    runs-on: ubuntu-latest
    needs: [syntax]
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install PySide6
        run: pip install PySide6

      - name: Run test suites
        env:
          QT_QPA_PLATFORM: offscreen
          STATABLE_DISABLE_MERMAID: '1'
        run: |
          python tests/test_v2_2_p1.py
          python tests/test_v2_2_p2.py
          python tests/test_v2_2_p3.py
          python tests/test_v2_2_p4a.py
          python tests/test_v2_2_p4b.py
          python tests/test_v2_2_p12_2.py
          python tests/test_v2_2_p12_5.py
          python tests/test_v2_2_p12_6.py

  # ==============================================================
  # Job 4: Generated C code verification
  # ==============================================================
  generated-code:
    name: Generated C code verification
    runs-on: ubuntu-latest
    needs: [syntax]
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install PySide6
        run: pip install PySide6

      - name: Generate C code from test XML
        run: |
          python -c "
          import sys
          sys.path.insert(0, '.')
          from codegen.c_code_generator import CCodeGenerator
          from codegen.config import CodeGenerationConfig
          from statable.xml_io import project_from_xml

          tabs, gd, _, _, _, ps = project_from_xml(
              'tests/data/v22_features_test3.xml')
          cfg = CodeGenerationConfig(**{
              k: v for k, v in ps.items()
              if hasattr(CodeGenerationConfig, k)
          })
          gen = CCodeGenerator(config=cfg)
          files = gen.generate_all_layers(tabs, gd)
          gen.save_generated_code(files, 'output')
          print(f'Saved {len(files)} files')
          "

      - name: Verify generated C code
        run: |
          python tools/verify_generated_code.py --root output
          # Expect: "TOTAL: errors=0, warnings=0"
```

---

#### 14.4.2 ローカルでの事前検証

CI に push する前に、ローカルで以下を実行することで **CI と同じ検証** が可能です。

```powershell
# Windows PowerShell
cd <project-root>

# Job 1
python tools\find_all_japanese.py

# Job 2
python -m compileall -q statable statable_gui codegen

# Job 3
$env:QT_QPA_PLATFORM = 'offscreen'
$env:STATABLE_DISABLE_MERMAID = '1'
python tests\test_v2_2_p1.py
python tests\test_v2_2_p2.py
python tests\test_v2_2_p3.py
python tests\test_v2_2_p4a.py
python tests\test_v2_2_p4b.py
python tests\test_v2_2_p12_2.py
python tests\test_v2_2_p12_5.py
python tests\test_v2_2_p12_6.py

# Job 4
python -c "import sys; sys.path.insert(0, '.'); from codegen.c_code_generator import CCodeGenerator; from codegen.config import CodeGenerationConfig; from statable.xml_io import project_from_xml; tabs, gd, _, _, _, ps = project_from_xml('tests/data/v22_features_test3.xml'); cfg = CodeGenerationConfig(**{k: v for k, v in ps.items() if hasattr(CodeGenerationConfig, k)}); gen = CCodeGenerator(config=cfg); files = gen.generate_all_layers(tabs, gd); gen.save_generated_code(files, 'output')"
python tools\verify_generated_code.py --root output
```

---

#### 14.4.3 CI 失敗時のトラブルシューティング

| ジョブ | 失敗症状 | 対応 |
|---|---|---|
| `no-japanese` | `Total: N line(s)` | `find_all_japanese.py` の出力を確認、該当箇所を英語化 |
| `syntax` | `SyntaxError` | 該当ファイルを修正、`compileall` で再確認 |
| `tests` | 特定テスト FAIL | ローカルで再現 → 修正 |
| `generated-code` | `errors > 0` | `verify_generated_code.py` の出力を確認、ジェネレータ修正 |

---

#### 14.4.4 依存関係

```yaml
syntax
  ├─→ tests
  └─→ generated-code
no-japanese  (独立)
```

`no-japanese` は並列実行可能。`tests` と `generated-code` は `syntax` 成功後に実行。

---

#### 14.4.5 将来拡張（v2.3 候補）

| 追加ジョブ | 内容 |
|---|---|
| `compile-c` | GCC で生成 C コードを実コンパイル（要 `gcc` インストール） |
| `mypy` | 型チェック |
| `pytest` | `pytest` 形式での統一実行 |
| `coverage` | カバレッジ計測 |
```

---

# 項目 5: Custom type `_t` 二重化の自動回避

## 5.1 問題の再確認

| 入力 | 現状の出力 | 参照側 | 結果 |
|---|---|---|---|
| `CustomTypeDef(name="SystemStatus_t")` | `SystemStatusT_t` | `SystemStatus_t` | ❌ 型名不一致 |
| `CustomTypeDef(name="SystemStatus")` | `SystemStatus_t` | `SystemStatus_t` | ✅ 一致 |

**原因**: `naming_convention.py::create_type_name()` が **末尾の `_t` を考慮せず** に PascalCase 変換 + `_t` 付与。

## 5.2 修正内容

`codegen/naming_convention.py` の `create_type_name()` を **冪等化**（1 メソッドのみ）。

### 変更前

```python
    @classmethod
    def create_type_name(cls, name):
        return cls.to_pascal_case(name) + "_t"
```

### 変更後

```python
    @classmethod
    def create_type_name(cls, name):
        """Create a C type name with '_t' suffix (idempotent).

        [v2.2.5 fix]
          If the name already ends with '_t', it is preserved as-is
          so that references match. Otherwise PascalCase + '_t' is applied.

        Examples:
            'SystemStatus'   -> 'SystemStatus_t'
            'SystemStatus_t' -> 'SystemStatus_t'   (not 'SystemStatusT_t')
            'sensor_data'    -> 'SensorData_t'
            'sensor_data_t'  -> 'sensor_data_t'    (preserved)
            ''               -> 'Unknown_t'
        """
        if not name:
            return "Unknown_t"
        if name.endswith('_t'):
            return name
        return cls.to_pascal_case(name) + "_t"
```

## 5.3 完全版ファイル: `codegen/naming_convention.py`

```python
# codegen/naming_convention.py
"""
C language naming convention module.

Version: 2.2.5 (2026-09-19)
  - Fix: create_type_name() is now idempotent.
    Names already ending in '_t' are preserved (avoids '_t_t' doubling
    such as 'SystemStatus_t' -> 'SystemStatusT_t').
"""

import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .code_templates import CodeTemplates
except ImportError:
    from code_templates import CodeTemplates


class CNamingConvention:
    """Class managing C naming conventions"""

    CONVERSION_PATTERNS = {
        'upper_snake': {
            'patterns': [
                (r'(.)([A-Z][a-z]+)', r'\1_\2'),
                (r'([a-z0-9])([A-Z])', r'\1_\2'),
            ],
            'transform': str.upper,
        },
        'lower_snake': {
            'patterns': [
                (r'(.)([A-Z][a-z]+)', r'\1_\2'),
                (r'([a-z0-9])([A-Z])', r'\1_\2'),
            ],
            'transform': str.lower,
        },
        'camel': {
            'split': r'[_-]',
            'first': str.lower,
            'rest': str.capitalize,
        },
        'pascal': {
            'split': r'[_-]',
            'first': str.capitalize,
            'rest': str.capitalize,
        },
    }

    C_KEYWORDS = {
        'auto', 'break', 'case', 'char', 'const', 'continue',
        'default', 'do', 'double', 'else', 'enum', 'extern',
        'float', 'for', 'goto', 'if', 'inline', 'int', 'long',
        'register', 'restrict', 'return', 'short', 'signed',
        'sizeof', 'static', 'struct', 'switch', 'typedef',
        'union', 'unsigned', 'void', 'volatile', 'while',
        '_Bool', '_Complex', '_Imaginary'
    }

    IDENTIFIER_RULES = {
        'variable': 'to_lower_snake',
        'function': 'to_pascal_case',
        'type': 'to_pascal_case',
        'enum': 'to_upper_snake',
        'macro': 'to_upper_snake',
    }

    def __init__(self):
        self.templates = CodeTemplates()
        self.strings = self.templates.STRINGS
        self.formats = self.templates.FORMATS

    @classmethod
    def to_snake_case(cls, name, upper=False):
        config = cls.CONVERSION_PATTERNS['upper_snake' if upper else 'lower_snake']
        result = name
        for pattern, replacement in config['patterns']:
            result = re.sub(pattern, replacement, result)
        return config['transform'](result)

    @classmethod
    def to_upper_snake(cls, name):
        return cls.to_snake_case(name, upper=True)

    @classmethod
    def to_lower_snake(cls, name):
        return cls.to_snake_case(name, upper=False)

    @classmethod
    def to_camel_case(cls, name):
        config = cls.CONVERSION_PATTERNS['camel']
        parts = re.split(config['split'], name)
        if not parts:
            return ""
        result = config['first'](parts[0])
        for part in parts[1:]:
            if part:
                result += config['rest'](part)
        return result

    @classmethod
    def to_pascal_case(cls, name):
        """Convert to PascalCase"""
        config = cls.CONVERSION_PATTERNS['pascal']
        parts = re.split(config['split'], name)
        if not parts:
            return ""

        result = ""
        for part in parts:
            if part:
                # If camelCase, capitalize first letter
                result += part[0].upper() + part[1:]
        return result

    @classmethod
    def sanitize_identifier(cls, name):
        if not name:
            return "_unnamed"
        if name[0].isdigit():
            name = '_' + name
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        if name in cls.C_KEYWORDS:
            name = name + '_'
        return name

    @classmethod
    def create_identifier(cls, name, kind='variable'):
        method_name = cls.IDENTIFIER_RULES.get(kind, 'to_lower_snake')
        method = getattr(cls, method_name)
        return cls.sanitize_identifier(method(name))

    @classmethod
    def create_type_name(cls, name):
        """Create a C type name with '_t' suffix (idempotent).

        [v2.2.5 fix]
          If the name already ends with '_t', it is preserved as-is
          so that references match. Otherwise PascalCase + '_t' is applied.

        Examples:
            'SystemStatus'   -> 'SystemStatus_t'
            'SystemStatus_t' -> 'SystemStatus_t'   (not 'SystemStatusT_t')
            'sensor_data'    -> 'SensorData_t'
            'sensor_data_t'  -> 'sensor_data_t'    (preserved)
            ''               -> 'Unknown_t'
        """
        if not name:
            return "Unknown_t"
        if name.endswith('_t'):
            return name
        return cls.to_pascal_case(name) + "_t"

    @classmethod
    def create_enum_value(cls, prefix, name):
        return cls.sanitize_identifier(prefix) + "_" + cls.to_upper_snake(name)

    @classmethod
    def create_function_name(cls, module, action):
        return cls.to_pascal_case(module) + "_" + cls.to_pascal_case(action)

    @classmethod
    def create_variable_name(cls, name):
        return cls.sanitize_identifier(cls.to_lower_snake(name))

    @classmethod
    def create_macro_name(cls, name):
        return cls.to_upper_snake(name)
```

**変更点**: `create_type_name()` の 1 メソッドのみ（+ docstring に v2.2.5 注記）。

## 5.4 検証テスト（新規 / `tests/test_v2_2_p12_7.py`）

```python
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
        ("SystemStatus_t",   "SystemStatus_t"),    # ★ 二重化回避
        ("SensorData",       "SensorData_t"),
        ("SensorData_t",     "SensorData_t"),      # ★
        ("sensor_data",      "SensorData_t"),
        ("sensor_data_t",    "sensor_data_t"),     # ★ 元の形式を保持
        ("",                 "Unknown_t"),
        ("my_type",          "MyType_t"),
        ("my_type_t",        "my_type_t"),         # ★
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
```

### 実行

```powershell
python tests\test_v2_2_p12_7.py
```

### 期待結果

```
  [PASS] create_type_name('SystemStatus') -> 'SystemStatus_t' (expected 'SystemStatus_t')
  [PASS] create_type_name('SystemStatus_t') -> 'SystemStatus_t' (expected 'SystemStatus_t')
  [PASS] create_type_name('SensorData') -> 'SensorData_t' (expected 'SensorData_t')
  [PASS] create_type_name('SensorData_t') -> 'SensorData_t' (expected 'SensorData_t')
  [PASS] create_type_name('sensor_data') -> 'SensorData_t' (expected 'SensorData_t')
  [PASS] create_type_name('sensor_data_t') -> 'sensor_data_t' (expected 'sensor_data_t')
  [PASS] create_type_name('') -> 'Unknown_t' (expected 'Unknown_t')
  [PASS] create_type_name('my_type') -> 'MyType_t' (expected 'MyType_t')
  [PASS] create_type_name('my_type_t') -> 'my_type_t' (expected 'my_type_t')

TOTAL: 9  PASSED: 9  FAILED: 0
```

## 5.5 仕様書 §10.1 への追記

```markdown
### 10.1 データモデル関連

| # | 制約 | 影響 |
|---|---|---|
| 1 | `StateType.CONCURRENT` / `REGION` の親子関係 | 生成コードでは未使用 |
| 2 | イベントの `params` | 生成コードでは未使用 |
| 3 | `Transition.action` フィールド | 互換用・未使用 |
| **4** | **Custom type 名の `_t` サフィックス** | **v2.2.5 で冪等化**（`SystemStatus_t` → `SystemStatus_t`、二重化回避） |
```

---

# 統合検証手順

```powershell
cd C:\Users\user\OneDrive\ドキュメント\GitHub\StaTable\code

# 1. 構文
python -m compileall -q statable statable_gui codegen

# 2. Custom type 冪等性テスト（新規）
python tests\test_v2_2_p12_7.py

# 3. 既存テスト回帰
python tests\test_v2_2_p1.py
python tests\test_v2_2_p2.py
python tests\test_v2_2_p3.py
python tests\test_v2_2_p4a.py
python tests\test_v2_2_p4b.py
python tests\test_v2_2_p12_2.py
python tests\test_v2_2_p12_5.py
python tests\test_v2_2_p12_6.py

# 4. 生成コード検証
python -c "import sys; sys.path.insert(0, '.'); from codegen.c_code_generator import CCodeGenerator; from codegen.config import CodeGenerationConfig; from statable.xml_io import project_from_xml; tabs, gd, _, _, _, ps = project_from_xml('tests/data/v22_features_test3.xml'); cfg = CodeGenerationConfig(**{k: v for k, v in ps.items() if hasattr(CodeGenerationConfig, k)}); gen = CCodeGenerator(config=cfg); files = gen.generate_all_layers(tabs, gd); gen.save_generated_code(files, 'output')"
python tools\verify_generated_code.py --root output

# 5. 英語化
python tools\find_all_japanese.py
```

## 期待結果

| 検証 | 期待 |
|---|---|
| `test_v2_2_p12_7.py` | **9/9 PASS** |
| 既存テスト | 457/457 PASS（変更なし） |
| 生成コード検証 | errors=0, warnings=0 |
| 日本語 | 0 行 |

**累積: 466/466 PASS**

---

# 引継ぎ資料 更新（差分）

`HANDOVER_v2.2.md` の末尾に以下を追記:

```markdown
## 15. v2.2.5 追加修正

### 15.1 修正サマリ

| # | 項目 | 修正 |
|---|---|---|
| 1 | Python 要件明記 | §1.3: 「3.9 以上」→「3.10 以上」（`kw_only=True` のため） |
| 2 | CI 組み込み | `.github/workflows/check.yml` 4 ジョブ |
| 3 | Custom type `_t` 二重化 | `naming_convention.py::create_type_name()` 冪等化 |

### 15.2 CI ジョブ

| ジョブ | 検証 | 失敗条件 |
|---|---|---|
| `no-japanese` | 日本語残存 | 1 行でも検出 |
| `syntax` | Python 構文 | `compileall` 失敗 |
| `tests` | ユニットテスト | 1 件 FAIL |
| `generated-code` | 生成 C コード | errors > 0 |

### 15.3 累積テスト

| Phase | テスト数 |
|---|---|
| v2.2.4 まで | 457 |
| **v2.2.5 追加** | +9（`test_v2_2_p12_7.py`） |
| **合計** | **466** |

### 15.4 変更ファイル（v2.2.5）

| # | ファイル | 変更 |
|---|---|---|
| 1 | `codegen/naming_convention.py` | `create_type_name()` 冪等化 |
| 2 | `tests/test_v2_2_p12_7.py` | **新規**（9 テスト） |
| 3 | `.github/workflows/check.yml` | **新規** |
| 4 | `HANDOVER_v2.2.md` | §15 追加 |
```

---

## 次のアクション

1. **`naming_convention.py` を完全版に置換**
2. **`tests/test_v2_2_p12_7.py` を配置**
3. **`.github/workflows/check.yml` を配置**
4. **仕様書 §1.3 / §10.1 / §14.4 を更新**
5. 上記「統合検証手順」を実行 → 結果を貼り付け

**結果を待っています。** 全 PASS なら **v2.2.5 正式版** として確定します。