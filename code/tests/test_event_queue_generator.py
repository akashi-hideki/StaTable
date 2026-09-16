# tests/test_event_queue_generator.py
"""
event_queue_generator.EventQueueGenerator のユニットテスト

【目的】
  イベントキュー生成の回帰防止:
    - generate_struct: buffer/head/tail/count を含む struct
    - generate_enqueue_function: 満杯チェック + エンキュー
    - generate_dequeue_function: 空チェック + デキュー
    - generate_all_code: 3 種を連結
    - 複数キュー対応

【対象】
  codegen/event_queue_generator.py
"""
import pytest

from statable.global_defs import GlobalDefinitions, EventQueueDef
from codegen.event_queue_generator import EventQueueGenerator


# ============================================================
# ヘルパー
# ============================================================

def _make_queue(name="MainQueue", size=8,
                element_type="EVENT_t",
                description="メインキュー"):
    return EventQueueDef(
        name=name,
        size=size,
        element_type=element_type,
        description=description,
    )


def _make_gd(queues=()):
    gd = GlobalDefinitions()
    for q in queues:
        gd.event_queues.append(q)
    return gd


# ============================================================
# generate_struct
# ============================================================

class TestStruct:

    def test_basic_structure(self):
        gen = EventQueueGenerator()
        q = _make_queue()
        result = gen.generate_struct(q)
        assert "typedef struct" in result
        # メンバ
        assert "buffer[8]" in result
        assert "head" in result
        assert "tail" in result
        assert "count" in result

    def test_struct_name_pascal(self):
        gen = EventQueueGenerator()
        q = _make_queue(name="main_queue")
        result = gen.generate_struct(q)
        # create_type_name の実装次第だが Pascal 化
        assert "MainQueue" in result or "Main_Queue" in result

    def test_custom_size(self):
        gen = EventQueueGenerator()
        q = _make_queue(size=16)
        result = gen.generate_struct(q)
        assert "buffer[16]" in result

    def test_description_comment(self):
        gen = EventQueueGenerator()
        q = _make_queue(description="テストキュー")
        result = gen.generate_struct(q)
        assert "テストキュー" in result

    def test_interrupt_safe_flag(self):
        gen = EventQueueGenerator()
        q = _make_queue()
        q.interrupt_safe = True
        result = gen.generate_struct(q)
        assert "interrupt_safe" in result

    def test_rtos_enabled_flag(self):
        gen = EventQueueGenerator()
        q = _make_queue()
        q.rtos_enabled = True
        result = gen.generate_struct(q)
        assert "rtos_enabled" in result


# ============================================================
# generate_enqueue_function
# ============================================================

class TestEnqueue:

    def test_basic_structure(self):
        gen = EventQueueGenerator()
        q = _make_queue()
        result = gen.generate_enqueue_function(q)
        assert "bool" in result
        assert "Enqueue" in result
        assert "queue == NULL" in result
        assert "return false" in result

    def test_full_check(self):
        gen = EventQueueGenerator()
        q = _make_queue(size=8)
        result = gen.generate_enqueue_function(q)
        # 満杯チェック
        assert "queue->count >= 8" in result

    def test_enqueue_body(self):
        gen = EventQueueGenerator()
        q = _make_queue(size=8)
        result = gen.generate_enqueue_function(q)
        # buffer[tail] = event; tail = (tail + 1) % size; count++
        assert "queue->buffer[queue->tail] = event;" in result
        assert "queue->tail = (queue->tail + 1) % 8;" in result
        assert "queue->count++;" in result

    def test_function_name(self):
        gen = EventQueueGenerator()
        q = _make_queue(name="main")
        result = gen.generate_enqueue_function(q)
        assert "EventQueue_Main_Enqueue" in result


# ============================================================
# generate_dequeue_function
# ============================================================

class TestDequeue:

    def test_basic_structure(self):
        gen = EventQueueGenerator()
        q = _make_queue()
        result = gen.generate_dequeue_function(q)
        assert "bool" in result
        assert "Dequeue" in result
        assert "queue == NULL" in result

    def test_empty_check(self):
        gen = EventQueueGenerator()
        q = _make_queue()
        result = gen.generate_dequeue_function(q)
        assert "queue->count == 0" in result

    def test_dequeue_body(self):
        gen = EventQueueGenerator()
        q = _make_queue(size=8)
        result = gen.generate_dequeue_function(q)
        # event ポインタ NULL チェック
        assert "if (event == NULL)" in result
        # 読み出し
        assert "*event = queue->buffer[queue->head];" in result
        assert "queue->head = (queue->head + 1) % 8;" in result
        assert "queue->count--;" in result

    def test_function_name(self):
        gen = EventQueueGenerator()
        q = _make_queue(name="main")
        result = gen.generate_dequeue_function(q)
        assert "EventQueue_Main_Dequeue" in result


# ============================================================
# generate_all_code
# ============================================================

class TestGenerateAllCode:

    def test_includes_all_three(self):
        gen = EventQueueGenerator()
        q = _make_queue()
        result = gen.generate_all_code(q)
        assert "typedef struct" in result
        assert "Enqueue" in result
        assert "Dequeue" in result


# ============================================================
# 複数キュー
# ============================================================

class TestMultipleQueues:

    def test_generate_all_structs(self):
        gen = EventQueueGenerator()
        gd = _make_gd(queues=[
            _make_queue(name="queue_a"),
            _make_queue(name="queue_b"),
        ])
        result = gen.generate_all_structs(gd)
        assert "QueueA" in result
        assert "QueueB" in result

    def test_generate_all_functions(self):
        gen = EventQueueGenerator()
        gd = _make_gd(queues=[
            _make_queue(name="main"),
        ])
        result = gen.generate_all_functions(gd)
        assert "EventQueue_Main_Enqueue" in result
        assert "EventQueue_Main_Dequeue" in result

    def test_generate_all(self):
        gen = EventQueueGenerator()
        gd = _make_gd(queues=[
            _make_queue(name="main"),
        ])
        result = gen.generate_all(gd)
        # 全て含まれる
        assert "typedef struct" in result
        assert "Enqueue" in result
        assert "Dequeue" in result

    def test_empty_gd(self):
        gen = EventQueueGenerator()
        gd = GlobalDefinitions()
        result = gen.generate_all(gd)
        assert result == ""


# ============================================================
# エッジケース
# ============================================================

class TestEdgeCases:

    def test_size_one(self):
        gen = EventQueueGenerator()
        q = _make_queue(size=1)
        result = gen.generate_struct(q)
        assert "buffer[1]" in result

    def test_large_size(self):
        gen = EventQueueGenerator()
        q = _make_queue(size=256)
        result = gen.generate_struct(q)
        assert "buffer[256]" in result

    def test_unnamed_queue(self):
        """名前空でもエラーにならない"""
        gen = EventQueueGenerator()
        q = _make_queue(name="")
        # クラッシュしないこと
        result = gen.generate_struct(q)
        assert "typedef struct" in result