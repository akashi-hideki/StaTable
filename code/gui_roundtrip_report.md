# GUI round-trip 自動テストレポート

- 対象 XML: 1 件

## サマリ

| XML | Status | 詳細 |
|---|---|---|
| isr_namespace_test.xml | ERROR | exception: [Errno 2] No such file or directory: 'C:\\Users\\user\\OneDrive\\ドキュメント\\GitHub\\StaTable\\code\\specs\\isr_namespace_test.xml' |

## isr_namespace_test.xml
- Status: **ERROR**
- Summary: exception: [Errno 2] No such file or directory: 'C:\\Users\\user\\OneDrive\\ドキュメント\\GitHub\\StaTable\\code\\specs\\isr_namespace_test.xml'

### 詳細
```
Traceback (most recent call last):
  File "C:\Users\user\OneDrive\ドキュメント\GitHub\StaTable\code\tests\test_gui_roundtrip.py", line 208, in gui_roundtrip_one
    orig_text = xml_path.read_text(encoding="utf-8")
  File "C:\Program Files\Python313\Lib\pathlib\_local.py", line 546, in read_text
    return PathBase.read_text(self, encoding, errors, newline)
           ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Program Files\Python313\Lib\pathlib\_abc.py", line 632, in read_text
    with self.open(mode='r', encoding=encoding, errors=errors, newline=newline) as f:
         ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Program Files\Python313\Lib\pathlib\_local.py", line 537, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\user\\OneDrive\\ドキュメント\\GitHub\\StaTable\\code\\specs\\isr_namespace_test.xml'

```

## 集計

- ERROR: 1