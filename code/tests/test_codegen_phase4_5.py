# tests/test_codegen_phase4_5.py
"""
イベントキュー・割り込み処理・タイマ生成のテスト
"""

import sys
import os
import importlib.util

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'codegen'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'statable'))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_sample_data():
    sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'codegen', 'sample_data.py')
    sample_module = load_module("phase45_sample", sample_path)
    return sample_module.SampleDataGenerator().get_sample_data()


def get_generator():
    cgen_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'codegen', 'c_code_generator.py')
    cgen_module = load_module("phase45_cgen", cgen_path)
    return cgen_module.CCodeGenerator()


class TestEventQueueGeneration:
    def test_event_queue_struct(self):
        sm, gd = get_sample_data()
        gen = get_generator()
        content = gen.generate_file('statable_event_queue.c', sm, gd)
        assert 'typedef struct' in content
        assert 'EventQueue' in content

class TestInterruptGeneration:
    def test_isr_generation(self):
        sm, gd = get_sample_data()
        gen = get_generator()
        content = gen.generate_file('statable_interrupt.c', sm, gd)
        assert 'ISR_' in content or '割り込み' in content

class TestTimerGeneration:
    def test_timer_struct(self):
        sm, gd = get_sample_data()
        gen = get_generator()
        content = gen.generate_file('statable_timer.c', sm, gd)
        assert 'TimerVariables_t' in content or 'g_system_tick' in content

class TestFullGeneration:
    def test_all_files_generated(self):
        sm, gd = get_sample_data()
        gen = get_generator()
        files = gen.generate_all(sm, gd)
        # 6 + 3 = 9ファイル
        assert len(files) == 9
        assert 'statable_event_queue.c' in files
        assert 'statable_interrupt.c' in files
        assert 'statable_timer.c' in files


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])