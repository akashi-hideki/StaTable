# tests/test_mermaid_gen.py
"""
mermaid_gen.generate_mermaid のユニットテスト

【目的】
  Mermaid ラベルサニタイズの回帰防止
  - タイトル / イベント名 / 条件式に含まれる特殊文字でパースエラーが出ないこと

【背景】
  v2.0 で "RETRY: battery_voltage >600" のようにタイトルに ":" が
  含まれると Mermaid がパースエラーを起こす問題を修正。
  _sanitize_label() で全角に置換して回避。
"""
import pytest

from statable.model import State, Event, Transition
from statable.state_machine import StateMachine
from statable.mermaid_gen import generate_mermaid, _sanitize_label


# ============================================================
# ヘルパー
# ============================================================

def _make_sm_with_transition(title="", event="GO", target="B",
                              condition="", source="A"):
    """
    1 遷移を持つ StateMachine を構築

    ★ 修正: イベントを sm.events に事前登録する
       （state_machine.add_transition は event が登録済みであることを要求）
    """
    sm = StateMachine()
    sm.add_state(State(name=source))
    if target:
        sm.add_state(State(name=target))
    if event:
        sm.add_event(Event(name=event))
    sm.add_transition(Transition(
        source=source,
        event=event,
        target=target,
        title=title,
        condition=condition,
    ))
    return sm


def _find_transition_line(mermaid_text: str, source: str, target: str) -> str:
    """特定の遷移行を抽出"""
    for line in mermaid_text.splitlines():
        if f"{source} --> {target}" in line:
            return line
    raise AssertionError(f"transition line not found: {source} --> {target}")


# ============================================================
# _sanitize_label のユニットテスト（全て PASS 済）
# ============================================================

class TestSanitizeLabel:

    def test_colon_replaced(self):
        """コロンが全角に置換される"""
        assert "：" in _sanitize_label("RETRY: battery")

    def test_brackets_replaced(self):
        """角括弧が全角に置換される"""
        assert "［" in _sanitize_label("[a]")
        assert "］" in _sanitize_label("[a]")

    def test_double_quote_replaced(self):
        """ダブルクォートがシングルに置換される"""
        assert '"' not in _sanitize_label('say "hi"')

    def test_newline_replaced(self):
        """改行が空白に置換される"""
        assert "\n" not in _sanitize_label("line1\nline2")

    def test_empty_string(self):
        """空文字列はそのまま空"""
        assert _sanitize_label("") == ""

    def test_none_safe(self):
        """None を渡してもエラーにならない"""
        assert _sanitize_label(None) == ""

    def test_consecutive_spaces_collapsed(self):
        """連続空白が 1 つに正規化される"""
        assert _sanitize_label("a    b") == "a b"


# ============================================================
# generate_mermaid の統合テスト（修正済）
# ============================================================

class TestGenerateMermaid:

    def test_basic_output(self):
        """基本構造が出力される"""
        sm = _make_sm_with_transition(title="起動", event="START")
        result = generate_mermaid(sm)
        assert result.startswith("stateDiagram-v2")
        assert "direction LR" in result
        assert "A --> B" in result

    def test_colon_in_title_does_not_break(self):
        """タイトル内の ':' がパースエラーを起こさない（本件の再発防止）"""
        sm = _make_sm_with_transition(
            title="RETRY: battery_voltage >600",
            event="RETRY",
        )
        result = generate_mermaid(sm)
        line = _find_transition_line(result, "A", "B")
        # 区切りの ":" は 1 個のみ（タイトル内は全角に置換済）
        assert line.count(":") == 1
        assert "：" in line

    def test_brackets_in_title(self):
        """タイトル内の '[' ']' が全角に置換される"""
        sm = _make_sm_with_transition(title="[TEST]", event="GO")
        result = generate_mermaid(sm)
        line = _find_transition_line(result, "A", "B")
        # 全角化された [TEST] が含まれること
        assert "［TEST］" in line

    def test_condition_with_colon(self):
        """条件式内の特殊文字も安全化される"""
        sm = _make_sm_with_transition(
            title="判定",
            condition="x ? 1 : 0",
        )
        result = generate_mermaid(sm)
        line = _find_transition_line(result, "A", "B")
        # 条件内の ":" は全角化 → 区切り ":" は 1 個のみ
        assert line.count(":") == 1

    def test_long_condition_truncated(self):
        """長い条件は短縮される"""
        long_cond = "x" * 100
        sm = _make_sm_with_transition(title="test", condition=long_cond)
        result = generate_mermaid(sm)
        assert "..." in result

    def test_empty_title_uses_target(self):
        """タイトルなしの遷移は target を表示"""
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_state(State(name="B"))
        sm.add_event(Event(name="GO"))
        sm.add_transition(Transition(source="A", event="GO", target="B"))
        result = generate_mermaid(sm)
        line = _find_transition_line(result, "A", "B")
        # target 名 B がラベルに含まれる
        assert "B" in line

    def test_initial_state(self):
        """initial_state が設定されていれば [*] 行が出る"""
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.set_initial("A")
        result = generate_mermaid(sm)
        assert "[*] --> A" in result

    def test_internal_transition(self):
        """target なし → note right of で出力"""
        sm = StateMachine()
        sm.add_state(State(name="A"))
        sm.add_event(Event(name="E"))
        sm.add_transition(Transition(
            source="A", event="E", target="", title="内部処理",
        ))
        result = generate_mermaid(sm)
        assert "note right of A" in result
        assert "internal" in result

    def test_all_special_chars_together(self):
        """すべての特殊文字を含むタイトルでもエラーにならない"""
        sm = _make_sm_with_transition(
            title='a:b[c]d"e`f\ng',
            event="EVT",
        )
        result = generate_mermaid(sm)
        # ラベル内の ":" が区切りと誤認されないこと
        line = _find_transition_line(result, "A", "B")
        assert line.count(":") == 1