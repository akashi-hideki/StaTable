# StaTable 想定質問と回答（FAQ）

**作成日**: 2026-10-12
**用途**: 中国企業・技術者からの問い合わせ対応
**対象**: WeChat、メール、GitHub Issues

---

## 1. 製品概要

### Q1-1: StaTable とは何ですか？

**A**: StaTable は、組込みシステム向けの状態機械設計ツールです。
GUI で状態遷移を設計すると、MISRA C:2012 に準拠した C99 コードを
自動生成します。

### Q1-2: 主な機能は？

**A**:
- 七層アーキテクチャ（Application + 4 Mw + Driver I/O）
- 表駆動型コード生成（状態 × 事件行列 → C99）
- ユーザーコード保護（marker 方式）
- Eclipse 統合（独立インストーラ）
- Mermaid 状態図の自動生成

### Q1-3: 対応言語は？

**A**: 英語、日本語、簡体中文の 3 言語です。
UI とドキュメントの両方が 3 言語対応しています。

---

## 2. インストール・環境

### Q2-1: インストール方法は？

**A**: 以下の 3 通りがあります。

**方法 A: ポータブル版（推奨）**
1. `StaTable-portable-v3.5.3-win64.zip` をダウンロード
2. 解凍
3. `StaTable\StaTable.exe` をダブルクリック
- **Python 不要**

**方法 B: pip インストール**
```
pip install statable
pip install statable[gui]   # GUI 付き
```

**方法 C: Eclipse 統合**
`StaTable-Eclipse-Installer-v0.1.1-win64.zip` をダウンロード

### Q2-2: 対応 OS は？

**A**:
- **Windows 10/11** — 完全対応
- **Linux (Ubuntu 22.04+)** — テスト済み
- **macOS** — 未検証

### Q2-3: Python のバージョンは？

**A**: Python 3.10 〜 3.13 に対応しています。

---

## 3. 技術仕様

### Q3-1: MISRA C のバージョンは？

**A**: MISRA C:2012 に対応しています。
cppcheck の公式 MISRA アドオンで検証済みです。

### Q3-2: 生成される C コードの規格は？

**A**: C99 準拠です。gcc と ARM GCC で構文検証済み、
ARM Cortex-M4 でリンク検証済みです。

### Q3-3: 対応 MCU は？

**A**:
- **STM32G4（Cortex-M4 + FPU）** ★ 推奨
- STM32G0 / F4 / F7
- GD32 などの国产替代

### Q3-4: ユーザーコード保護とは？

**A**: 生成された C コードに手書きのコードを追加しても、
再生成時に消えない仕組みです。
`[[STABLE_USER_CODE_START]]` / `[[STABLE_USER_CODE_END]]`
マーカーで囲まれた部分が保護されます。

### Q3-5: テスト状況は？

**A**:
- 49 テストスイート / 1873 PASS / 0 FAIL
- mypy: 0 errors in 118 files
- CI: 11 ジョブ green

---

## 4. ライセンス・価格

### Q4-1: ライセンスは？

**A**: Apache License 2.0 です。
商用利用、改変、配布、再許諾が可能です。

### Q4-2: 価格は？

**A**: 現時点では無償公開しています。
商用ライセンス、OEM、カスタム開発については個別にご相談ください。

### Q4-3: 商用利用は可能？

**A**: はい、可能です。
Apache-2.0 ライセンスのため、商用製品への組み込みも問題ありません。

### Q4-4: サポートは？

**A**: GitHub Issues で受け付けています。
有償サポートについては個別にご相談ください。

---

## 5. 中国市場関連

### Q5-1: 中国語ドキュメントは？

**A**:
- `TUTORIAL_zh.md`（57.2 KB） — 完全なチュートリアル
- `USER_CODE_GUIDE_zh-CN.md`（11.7 KB） — ユーザーコード保護
- `README_zh.md` — 概要

### Q5-2: Eclipse との統合方法は？

**A**: Eclipse Installer を使用します。
Eclipse 4.41 + ARM Cross GCC で動作確認済みです。
QEMU で実機検証も可能です。

### Q5-3: 下载速度が遅い場合は？

**A**: GitHub へのアクセスが遅い場合は、
以下のミラーをご利用ください：
- GitHub プロキシ: `https://ghp.ci/https://github.com/akashi-hideki/StaTable`
- 阿里云盘: （準備中）

---

## 6. 技術サポート

### Q6-1: バグ報告は？

**A**: GitHub Issues にて受け付けています。
https://github.com/akashi-hideki/StaTable/issues

### Q6-2: 機能リクエストは？

**A**: 同上。GitHub Issues でお願いします。

### Q6-3: ドキュメントの誤りは？

**A**: GitHub Issues または Pull Request でお知らせください。

---

## 7. ビジネス関連

### Q7-1: 買収・ライセンスの相談は？

**A**: 個別にご連絡ください。
GitHub プロフィール、または WeChat でご相談ください。

### Q7-2: OEM 契約は可能？

**A**: はい、可能です。条件については個別にご相談ください。

### Q7-3: カスタム開発は？

**A**: 内容により対応可能です。詳細をお知らせください。

---

## 8. よくある誤解

### Q8-1: 「無償 = サポートなし」ですか？

**A**: いいえ。GitHub Issues でのサポートは提供しています。
有償サポートは別途ご相談ください。

### Q8-2: 「個人開発 = 品質が低い」ですか？

**A**: いいえ。StaTable は：
- 49 テストスイート / 1873 PASS
- mypy 0 errors
- ARM Cortex-M4 リンク検証済み
- CI 11 ジョブ green

商用グレードの品質を維持しています。

### Q8-3: 「中国語対応 = 翻訳のみ」ですか？

**A**: いいえ。中国語 UI、中国語ドキュメント、
中国語チュートリアルが完全に揃っています。

---

## 9. 連絡先

- **GitHub**: https://github.com/akashi-hideki/StaTable
- **PyPI**: https://pypi.org/project/statable/
- **WeChat**: 個別にご連絡ください
- **Email**: akashi.hideki@gmail.com

---

*本 FAQ は、中国企業・技術者からの問い合わせ対応のために作成されました。*
