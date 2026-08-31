# tests/test_code_merger.py
"""
CodeMerger のテスト
ユーザーコード保護機能の検証
"""

import sys
import os
import importlib.util
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'codegen'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'statable'))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def merger():
    merger_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'codegen', 'code_merger.py')
    module = load_module("test_code_merger", merger_path)
    return module.CodeMerger()


class TestFileUserCode:
    """ファイル全体のユーザーコードテスト"""
    
    def test_extract_file_user_code(self, merger):
        content = """#include "test.h"

/* [[STABLE_USER_CODE_START]] */
#include "my_header.h"
#define MY_MACRO 100
/* [[STABLE_USER_CODE_END]] */

void test(void) {}
"""
        user_code = merger.extract_file_user_code(content)
        assert '#include "my_header.h"' in user_code
        assert '#define MY_MACRO 100' in user_code
    
    def test_extract_no_user_code(self, merger):
        content = """#include "test.h"

void test(void) {}
"""
        user_code = merger.extract_file_user_code(content)
        assert user_code == ""
    
    def test_inject_file_user_code(self, merger):
        generated = """#include "test.h"

void test(void) {}
"""
        user_code = '#include "my_header.h"\n#define MY_MACRO 100'
        
        result = merger.inject_file_user_code(generated, user_code)
        assert 'STABLE_USER_CODE_START' in result
        assert '#include "my_header.h"' in result
        assert 'STABLE_USER_CODE_END' in result


class TestFuncUserCode:
    """関数単位のユーザーコードテスト"""
    
    def test_extract_func_user_code(self, merger):
        content = """void RoleFunc_PowerOn(STATE_t *current_state, SystemContext_t *ctx)
{
    /* [[STABLE_USER_CODE_START:PowerOn]] */
    ctx->flags.EVT_POWER_ON_REQ = 1;
    /* [[STABLE_USER_CODE_END:PowerOn]] */
    return;
}
"""
        user_code = merger.extract_func_user_code(content, "PowerOn")
        assert 'ctx->flags.EVT_POWER_ON_REQ = 1;' in user_code
    
    def test_extract_all_func_user_codes(self, merger):
        content = """void RoleFunc_PowerOn(void) {
    /* [[STABLE_USER_CODE_START:PowerOn]] */
    // PowerOn実装
    /* [[STABLE_USER_CODE_END:PowerOn]] */
}

void RoleFunc_Start(void) {
    /* [[STABLE_USER_CODE_START:Start]] */
    // Start実装
    /* [[STABLE_USER_CODE_END:Start]] */
}
"""
        codes = merger.extract_all_func_user_codes(content)
        assert 'PowerOn' in codes
        assert 'Start' in codes
        assert '// PowerOn実装' in codes['PowerOn']
        assert '// Start実装' in codes['Start']
    
    def test_inject_func_user_code(self, merger):
        generated = """void RoleFunc_PowerOn(STATE_t *current_state, SystemContext_t *ctx)
{
    /* TODO: 実装を記述すること */
    (void)current_state;
    (void)ctx;
    return;
}
"""
        user_code = 'ctx->flags.EVT_POWER_ON_REQ = 1;'
        
        result = merger.inject_func_user_code(generated, "PowerOn", user_code)
        assert 'STABLE_USER_CODE_START:PowerOn' in result
        assert 'ctx->flags.EVT_POWER_ON_REQ = 1;' in result
        assert 'STABLE_USER_CODE_END:PowerOn' in result


class TestMergeFile:
    """ファイルマージのテスト"""
    
    def test_merge_new_file(self, merger):
        """既存コードがない場合"""
        generated = """#include "test.h"

void test(void) {}
"""
        result = merger.merge_file(generated, None)
        assert result == generated
    
    def test_merge_with_file_user_code(self, merger):
        """ファイル全体のユーザーコードがある場合"""
        generated = """#include "test.h"

void test(void) {}
"""
        existing = """#include "test.h"

/* [[STABLE_USER_CODE_START]] */
#include "my_header.h"
/* [[STABLE_USER_CODE_END]] */

void test(void) {}
"""
        result = merger.merge_file(generated, existing)
        assert '#include "my_header.h"' in result
        assert 'STABLE_USER_CODE_START' in result
    
    def test_merge_with_func_user_code(self, merger):
        """関数単位のユーザーコードがある場合"""
        generated = """void RoleFunc_PowerOn(void) {
    /* TODO: 実装を記述すること */
    return;
}
"""
        existing = """void RoleFunc_PowerOn(void) {
    /* [[STABLE_USER_CODE_START:PowerOn]] */
    ctx->flags.EVT_POWER_ON_REQ = 1;
    /* [[STABLE_USER_CODE_END:PowerOn]] */
    return;
}
"""
        result = merger.merge_file(generated, existing)
        assert 'ctx->flags.EVT_POWER_ON_REQ = 1;' in result


class TestUserCodeSummary:
    """ユーザーコード概要のテスト"""
    
    def test_has_user_code(self, merger):
        content = """/* [[STABLE_USER_CODE_START]] */
test
/* [[STABLE_USER_CODE_END]] */
"""
        assert merger.has_user_code(content)
    
    def test_no_user_code(self, merger):
        content = "void test(void) {}"
        assert not merger.has_user_code(content)
    
    def test_get_summary(self, merger):
        content = """/* [[STABLE_USER_CODE_START]] */
file code
/* [[STABLE_USER_CODE_END]] */

void RoleFunc_Test(void) {
    /* [[STABLE_USER_CODE_START:Test]] */
    func code
    /* [[STABLE_USER_CODE_END:Test]] */
}
"""
        summary = merger.get_user_code_summary(content)
        assert summary['file_user_code'] > 0
        assert summary['func_user_codes'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])