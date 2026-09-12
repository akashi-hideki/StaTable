# codegen/code_templates.py
"""
コード生成用テンプレート定義（多層ステートマシン対応版）
すべての固定文字列を一元管理する
"""

class CodeTemplates:
    """コード生成用テンプレート辞書"""
    
    # ===== 基本文字列定義 =====
    STRINGS = {
        'section_line': '/*==============================================================*/',
        'indent_1': '    ',
        'indent_2': '        ',
        'indent_3': '            ',
        'newline': '\n',
        'blank_line': '',
        'typedef': 'typedef',
        'struct': 'struct',
        'enum': 'enum',
        'include': '#include',
        'define': '#define',
        'ifndef': '#ifndef',
        'endif': '#endif',
        'return': 'return',
        'void': 'void',
        'static': 'static',
        'const': 'const',
        'switch': 'switch',
        'case': 'case',
        'break': 'break',
        'default': 'default',
        'if': 'if',
        'else': 'else',
        'todo': 'TODO: 実装を記述すること',
        'unused_arg': '未使用引数の警告抑制',
        'auto_generated': 'StaTableにより自動生成されたコード',
        'no_edit': '手動での編集は推奨しない',
        'edit_in_statable': '変更する場合はStaTableで行うこと',
        'log_debug': 'LOG_DEBUG',
        'log_info': 'LOG_INFO',
        'log_warning': 'LOG_WARNING',
        'log_error': 'LOG_ERROR',
    }
    
    # ===== セクションヘッダ定義 =====
    SECTION_HEADERS = {
        'include': 'インクルードファイル',
        'type_defs': '型定義',
        'custom_types': 'ユーザー定義型',
        'system_structs': 'システム構造体',
        'transition_context': '遷移コンテキスト',
        'pending_event': '保留イベント制御',
        'layer_types': '層別型定義',
        'function_decls': '関数宣言',
        'role_functions': 'ロール関数宣言',
        'role_impl': 'ロール関数実装',
        'transition_table': '状態遷移テーブル',
        'transition_cells': 'セル単位遷移関数',
        'transition_func': '状態遷移関数',
        'get_next_event': 'イベント取得関数',
        'init_func': '初期化関数',
        'var_macros': '変数アクセスマクロ',
        'super_include': 'スーパーインクルード',
        'mutex_impl': 'ミューテックス実装',
        'semaphore_impl': 'セマフォ実装',
        'queue_impl': 'キュー実装',
        'critical_section_impl': 'クリティカルセクション実装',
    }
    
    # ===== 構造体コメント定義 =====
    STRUCT_COMMENTS = {
        'system_data': {'title': 'グローバル変数構造体', 'description': 'システム全体で共有する変数を管理'},
        'event_flags': {'title': 'イベントフラグ構造体', 'description': 'イベント発生を示すフラグを管理'},
        'system_context': {'title': 'システム全体構造体', 'description': 'グローバル変数とイベントフラグを統合管理'},
        'transition_cell': {'title': '遷移セル構造体', 'description': '状態遷移テーブルの1セルを表す'},
        'transition_context': {'title': '遷移コンテキスト構造体', 'description': '遷移元状態とイベントを保持'},
    }
    
    # ===== 列挙型コメント定義 =====
    ENUM_COMMENTS = {
        'state': {'title': '状態定義', 'description': '状態遷移の状態を表す列挙型'},
        'event': {'title': 'イベント定義', 'description': '状態遷移を発生させるイベントの列挙型'},
        'flag': {'title': 'イベントフラグ定義', 'description': 'イベントフラグの識別子を表す列挙型'},
    }
    
    # ===== 型名定義 =====
    TYPE_NAMES = {
        'state': 'STATE_t',
        'event': 'EVENT_t',
        'flag': 'FLAG_t',
        'system_data': 'SystemData_t',
        'event_flags': 'EventFlags_t',
        'system_context': 'SystemContext_t',
        'transition_cell': 'TransitionCell_t',
        'transition_table': 'transition_matrix',
        # ★ 多層対応（層名は動的に付加）
        'layer_state_prefix': 'STATE_',
        'layer_event_prefix': 'EVENT_',
        'layer_transition_context_prefix': 'TransitionContext_',
        'layer_process_prefix': 'StateMachine_Process_',
        'layer_get_next_event_prefix': 'StateMachine_GetNextEvent_',
        'layer_role_func_prefix': 'RoleFunc_',
        'layer_transition_func_prefix': 'transition_',
    }
    
    # ===== 関数名定義 =====
    FUNCTION_NAMES = {
        'state_machine_process': 'StateMachine_Process',
        'system_context_init': 'SystemContext_Init',
        'role_func_prefix': 'RoleFunc',
        'action_prefix': 'Action',
        'condition_prefix': 'Condition',
        'get_next_event_prefix': 'StateMachine_GetNextEvent',
        'layer_process_prefix': 'StateMachine_Process_',
    }
    
    # ===== マクロ名定義 =====
    MACRO_NAMES = {
        'data_prefix': 'DATA_',
        'flag_prefix': 'FLAG_',
        'max_suffix': '_MAX',
        'fire_event': 'FIRE_EVENT',
        'max_consecutive_pending_events': 'MAX_CONSECUTIVE_PENDING_EVENTS',
    }
    
    # ===== フォーマットテンプレート =====
    FORMATS = {
        'section_header': '{line}\n *  {title}\n{line}',
        'file_header': '''/**
 * @file    {filename}
 * @brief   {description}
 *
 * @note    {auto_generated}
 *          - {no_edit}
 *          - {edit_in_statable}
 *
 * @date    {date}
 */''',
        'include_guard_start': '#ifndef {guard_macro}\n#define {guard_macro}\n',
        'include_guard_end': '#endif /* {guard_macro} */',
        'struct_start': 'typedef struct {',
        'struct_end': '} {type_name};',
        'enum_start': 'typedef enum {',
        'enum_end': '} {type_name};',
        'enum_value': '{name} = {value},',
        'enum_value_with_comment': '{name} = {value},    /* {comment} */',
        'enum_max': '{name}           /* {comment} */',
        'data_macro': '#define DATA_{var_name}(ctx)    ((ctx)->data.{var_name})',
        'flag_macro': '#define FLAG_{flag_name}(ctx)   ((ctx)->flags.{flag_name})',
        'group_separator': '/* === {group_name} === */',
        'member_normal': '{indent}{type} {name};',
        'member_array': '{indent}{type} {name}[{size}];',
        'member_bitfield': '{indent}{type} {name} : {width};',
        'inline_comment': '{indent}/* {comment} */',
        'title_comment': '{indent}/* Title: {title} */',
    }
    
    # ===== ★ 多層ステートマシン用テンプレート =====
    
    # 層ごとの型定義ヘッダ用テンプレート
    LAYER_TEMPLATES = {
        'types_header_comment': '''/**
 * @file    statable_types_{layer}.h
 * @brief   {layer}層の型定義
 */''',
        'state_enum_comment': '/* {layer}層の状態定義 */',
        'event_enum_comment': '/* {layer}層のイベント定義 */',
        'transition_context_comment': '/* {layer}層の遷移コンテキスト */',
        'transition_context_struct': '''typedef struct {{
    STATE_{layer}_t from_state;
    EVENT_{layer}_t event;
}} TransitionContext_{layer}_t;''',
    }
    
    # 共通型ヘッダ用テンプレート
    COMMON_TYPES_TEMPLATES = {
        'system_context': '''typedef struct {{
    SystemData_t data;              /* グローバル変数 */
    EventFlags_t flags;             /* イベントフラグ */
    uint16_t pending_event;         /* 保留中のイベント */
    bool pending_event_valid;       /* 保留イベント有効フラグ */
}} SystemContext_t;''',
        'fire_event_macro': '''#define FIRE_EVENT(ctx, evt)  do {{ \\
    (ctx)->pending_event = (uint16_t)(evt); \\
    (ctx)->pending_event_valid = true; \\
}} while(0)''',
        'max_consecutive_pending_events': '''#ifndef MAX_CONSECUTIVE_PENDING_EVENTS
#define MAX_CONSECUTIVE_PENDING_EVENTS 16
#endif''',
    }
    
    # セル単位遷移関数用テンプレート
    TRANSITION_CELL_TEMPLATES = {
        'cell_func_comment': '''/**
 * @brief  セル遷移: {state} -[{event}]-> {target}
 */''',
        'cell_func_signature': 'static STATE_{layer}_t {func_name}(',
        'cell_func_args': '''    const TransitionContext_{layer}_t *transition,
    SystemContext_t *ctx''',
        'cell_func_open': ''')
{
    STATE_{layer}_t next_state = transition->from_state;''',
        'condition_if': '    if ({condition}) {{',
        'condition_if_true': '    if (1) {{   /* 条件なし遷移 */',
        'pre_actions': '        /* pre_actions */',
        'action_call': '        {func_name}(transition, ctx);',
        'target_assign': '        next_state = STATE_{layer}_{target};',
        'else_block': '    else {',
        'else_comment': '        /* else_actions */',
        'else_target_assign': '        next_state = STATE_{layer}_{else_target};',
        'else_not_set': '        /* else遷移先未設定 */',
        'cell_func_close': '''    return next_state;
}''',
    }
    
    # 遷移テーブル用テンプレート
    TRANSITION_TABLE_TEMPLATES = {
        'table_typedef': 'typedef STATE_{layer}_t (*TransitionFunc_{layer}_t)(\n    const TransitionContext_{layer}_t *, SystemContext_t *);',
        'table_start': 'static const TransitionFunc_{layer}_t transition_table_{layer}\n    [STATE_{layer}_MAX][EVENT_{layer}_MAX] = {{',
        'table_entry': '    [STATE_{layer}_{state}][EVENT_{layer}_{event}] = \n        {func_name},',
        'table_null_comment': '    /* [{state}][{event}] = NULL (遷移なし) */',
        'table_end': '};',
    }
    
    # 状態遷移関数用テンプレート
    PROCESS_FUNC_TEMPLATES = {
        'func_comment': '''/**
 * @brief  {layer}層の状態遷移処理
 * @param  current_state  現在の状態
 * @param  event          発生したイベント
 * @param  ctx            システムコンテキストポインタ
 * @return 遷移後の状態
 */''',
        'func_signature': 'STATE_{layer}_t StateMachine_Process_{layer}(',
        'func_args': '''    STATE_{layer}_t current_state,
    EVENT_{layer}_t event,
    SystemContext_t *ctx''',
        'func_open': ''')
{
    TransitionContext_{layer}_t transition = {
        .from_state = current_state,
        .event = event,
    };
    TransitionFunc_{layer}_t func = transition_table_{layer}[current_state][event];''',
        'func_null_check': '''    if (func != NULL) {
        return func(&transition, ctx);
    }''',
        'func_return': '''    return current_state;
}''',
    }
    
    # GetNextEvent 用テンプレート
    GET_NEXT_EVENT_TEMPLATES = {
        'func_comment': '''/**
 * @brief  {layer}層の次のイベントを取得（保留イベント優先）
 * @param  ctx  システムコンテキストポインタ
 * @return 次のイベント（保留なしの場合は EVENT_{layer}_NONE）
 */''',
        'func_signature': 'EVENT_{layer}_t StateMachine_GetNextEvent_{layer}(SystemContext_t *ctx)',
        'func_open': '{',
        'consecutive_count': '    static uint8_t consecutive_count = 0;',
        'pending_check': '''    if (ctx->pending_event_valid) {
        consecutive_count++;
        if (consecutive_count > MAX_CONSECUTIVE_PENDING_EVENTS) {
            LOG_ERROR("Pending event chain too long (%d)", consecutive_count);
            ctx->pending_event_valid = false;
            consecutive_count = 0;
            return EVENT_{layer}_NONE;
        }
        EVENT_{layer}_t evt = (EVENT_{layer}_t)ctx->pending_event;
        ctx->pending_event_valid = false;
        return evt;
    }
    consecutive_count = 0;
    return EVENT_{layer}_NONE;''',
        'func_close': '}',
    }
    
    # ロール関数用テンプレート（新シグネチャ）
    ROLE_FUNC_TEMPLATES = {
        'decl_comment': '''/**
 * @brief  ロール関数: {title}
 * @param  transition  遷移コンテキスト
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */''',
        'decl_signature': 'int RoleFunc_{layer}_{name}(',
        'decl_args': '''    const TransitionContext_{layer}_t *transition,
    SystemContext_t *ctx''',
        'decl_semicolon': ');',
        'impl_open': ''')
{
    (void)transition;  /* 未使用引数の警告抑制 */
    (void)ctx;         /* 未使用引数の警告抑制 */
    /* TODO: 実装を記述すること */''',
        'impl_user_marker_start': '    /* [[STABLE_USER_CODE_START:{name}]] */',
        'impl_user_marker_end': '    /* [[STABLE_USER_CODE_END:{name}]] */',
        'impl_return': '''    return 0;  /* デフォルト値 */
}''',
    }
    
        # スーパーインクルード用テンプレート
    SUPER_INCLUDE_TEMPLATES = {
        'file_comment': '''/**
 * @file    {filename}
 * @brief   StaTable 生成コード一括インクルード
 *
 * @note    このファイルは以下のファイルからのみインクルード可能:
 *          - ユーザーの main.c
 *          - プロジェクトの .c ファイル
 *          ※ 生成コードの .h ファイルからはインクルード禁止
 */''',
        'guard_start': '#ifndef STATABLE_ALL_H\n#define STATABLE_ALL_H\n',
        'common_section': '/* ---- 共通ヘッダ ---- */',
        'layer_section': '/* ---- 層ごとのヘッダ ---- */',
        'project_section': '/* ---- プロジェクトヘッダ ---- */',
        'external_section': '/* ---- 外部インクルード（ユーザー指定） ---- */',
        'user_section': '/* ---- ユーザー追加インクルード ---- */',
        'user_marker_start': '/* [[STABLE_USER_INCLUDES_START]] */',
        'user_marker_end': '/* [[STABLE_USER_INCLUDES_END]] */',
        'guard_end': '#endif /* STATABLE_ALL_H */',
        # ★ extern 宣言用
        'extern_var_section': '/* ---- スーパーループ変数（extern） ---- */',
        'extern_context': 'extern SystemContext_t g_ctx;',
        'extern_state': 'extern STATE_{layer}_t g_{layer}_state;',
        'extern_state_nolayer': 'extern STATE_t g_state;',
        'extern_func_section': '/* ---- スーパーループ関数 ---- */',
        'extern_init': 'void {project_name}_Init(void);',
        'extern_run': 'void {project_name}_Run(void);',
    }
    
    # スーパーループ用テンプレート（extern 対応版）
    SUPER_LOOP_TEMPLATES = {
        'file_comment': '''/**
 * @file    {project_name}_run.c
 * @brief   ステートマシン スーパーループ
 *
 * @note    このファイルはユーザーが編集しないこと
 *          ハードウェア初期化等は main.c で行い、本ファイルを呼び出す
 */''',
        'include': '#include "statable_all.h"',
        'context_var': 'SystemContext_t g_ctx;',
        'state_var': 'STATE_{layer}_t g_{layer}_state;',
        'state_var_nolayer': 'STATE_t g_state;',
        'init_func_comment': '''/**
 * @brief  ステートマシン初期化
 * @note   各層のステートマシンを優先度昇順で初期化
 */''',
        'init_func_signature': 'void {project_name}_Init(void)',
        'init_func_open': '{',
        'init_context': '    SystemContext_Init(&g_ctx);',
        'init_state': '    g_{layer}_state = STATE_{layer}_{initial};',
        'init_state_nolayer': '    g_state = STATE_{initial};',
        'init_func_close': '}',
        'run_func_comment': '''/**
 * @brief  ステートマシン メインループ
 */''',
        'run_func_signature': 'void {project_name}_Run(void)',
        'run_func_open': '{',
        'run_while': '    while (1) {',
        'run_block': '''        EVENT_{layer}_t evt = StateMachine_GetNextEvent_{layer}(&g_ctx);
        if (evt != EVENT_{layer}_NONE) {{
            g_{layer}_state = StateMachine_Process_{layer}(g_{layer}_state, evt, &g_ctx);
        }}''',
        'run_block_nolayer': '''        EVENT_t evt = StateMachine_GetNextEvent(&g_ctx);
        if (evt != EVENT_NONE) {
            g_state = StateMachine_Process(g_state, evt, &g_ctx);
        }''',
        'run_while_close': '    }',
        'run_func_close': '}',
    }
    
    # ===== デバッグログメッセージ定義 =====
    DEBUG_MESSAGES = {
        'function_entry': 'Enter {func_name}: state={state}, event={event}',
        'function_exit': 'Exit {func_name}: next_state={next_state}',
        'condition_check': 'Check condition: {condition_name}',
        'condition_not_met': 'Condition not met',
        'action_execute': 'Execute action: {action_name}',
        'transition': 'Transition: {from_state} -> {to_state} (event: {event})',
        'no_transition': 'No transition: state={state}, event={event}',
        'null_pointer': 'NULL pointer: {var_name}',
        'out_of_range': 'Out of range: {var_name}={value}, max={max}',
        'pending_event_too_long': 'Pending event chain too long ({count})',
    }
    
    # ===== OSAL関連テンプレート（既存のまま） =====
    OSAL = {
        # OS種別定義
        'os_types': {
            'non_rtos': {'name': 'NonRTOS', 'description': 'RTOSなし（ベアメタル）', 'header': 'osal.h', 'source': 'osal.c'},
            'freertos': {'name': 'FreeRTOS', 'description': 'FreeRTOS', 'header': 'osal_freertos.h', 'source': 'osal_freertos.c'},
            'threadx': {'name': 'ThreadX', 'description': 'Azure RTOS ThreadX', 'header': 'osal_threadx.h', 'source': 'osal_threadx.c'},
        },
        
        # ヘッダファイルテンプレート
        'header': {
            'file_comment': '''/**
 * @file    {filename}
 * @brief   OSAL（OS抽象化レイヤ）- {os_name}
 */''',
            'include_guard_start': '#ifndef {guard_name}\n#define {guard_name}\n',
            'include_guard_end': '#endif /* {guard_name} */',
            'type_defs_comment': '/* OSAL型定義 */',
            'status_enum': '''typedef enum {
    OSAL_OK = 0,
    OSAL_ERROR,
    OSAL_TIMEOUT,
    OSAL_BUSY,
} OSAL_Status_t;''',
            'mutex_type_nonrtos': '''typedef struct {
    volatile bool locked;
} OSAL_Mutex_t;''',
            'semaphore_type_nonrtos': '''typedef struct {
    volatile uint32_t count;
    volatile uint32_t max_count;
} OSAL_Semaphore_t;''',
            'queue_type_nonrtos': '''typedef struct {
    void *buffer;
    uint32_t size;
    uint32_t item_size;
    volatile uint32_t head;
    volatile uint32_t tail;
    volatile uint32_t count;
} OSAL_Queue_t;''',
            'mutex_decls': '''OSAL_Status_t OSAL_Mutex_Create(OSAL_Mutex_t *mutex);
OSAL_Status_t OSAL_Mutex_Lock(OSAL_Mutex_t *mutex, uint32_t timeout_ms);
OSAL_Status_t OSAL_Mutex_Unlock(OSAL_Mutex_t *mutex);''',
            'semaphore_decls': '''OSAL_Status_t OSAL_Semaphore_Create(OSAL_Semaphore_t *sem, uint32_t max_count, uint32_t initial_count);
OSAL_Status_t OSAL_Semaphore_Take(OSAL_Semaphore_t *sem, uint32_t timeout_ms);
OSAL_Status_t OSAL_Semaphore_Give(OSAL_Semaphore_t *sem);''',
            'queue_decls': '''OSAL_Status_t OSAL_Queue_Create(OSAL_Queue_t *queue, void *buffer, uint32_t size, uint32_t item_size);
OSAL_Status_t OSAL_Queue_Send(OSAL_Queue_t *queue, const void *item, uint32_t timeout_ms);
OSAL_Status_t OSAL_Queue_Receive(OSAL_Queue_t *queue, void *item, uint32_t timeout_ms);''',
            'critical_decls': '''void OSAL_Critical_Enter(void);
void OSAL_Critical_Exit(void);''',
            'freertos_includes': '#include "FreeRTOS.h"\n#include "semphr.h"\n#include "queue.h"',
            'threadx_includes': '#include "tx_api.h"',
        },
        
        # ソースファイルテンプレート
        'source': {
            'file_comment': '''/**
 * @file    {filename}
 * @brief   OSAL（OS抽象化レイヤ）- {os_name} 実装
 */''',
            'mutex_section_comment': '/* ミューテックス実装 */',
            'semaphore_section_comment': '/* セマフォ実装 */',
            'queue_section_comment': '/* キュー実装 */',
            'critical_section_comment': '/* クリティカルセクション実装 */',
            
            # NonRTOS ミューテックス実装
            'mutex_create_nonrtos': '''OSAL_Status_t OSAL_Mutex_Create(OSAL_Mutex_t *mutex)
{
    if (mutex == NULL) {
        return OSAL_ERROR;
    }
    mutex->locked = false;
    return OSAL_OK;
}''',
            'mutex_lock_nonrtos': '''OSAL_Status_t OSAL_Mutex_Lock(OSAL_Mutex_t *mutex, uint32_t timeout_ms)
{
    (void)timeout_ms;  /* NonRTOSでは使用しない */
    if (mutex == NULL) {
        return OSAL_ERROR;
    }
    if (mutex->locked) {
        return OSAL_BUSY;
    }
    mutex->locked = true;
    return OSAL_OK;
}''',
            'mutex_unlock_nonrtos': '''OSAL_Status_t OSAL_Mutex_Unlock(OSAL_Mutex_t *mutex)
{
    if (mutex == NULL) {
        return OSAL_ERROR;
    }
    mutex->locked = false;
    return OSAL_OK;
}''',
            
            # NonRTOS セマフォ実装
            'semaphore_create_nonrtos': '''OSAL_Status_t OSAL_Semaphore_Create(OSAL_Semaphore_t *sem, uint32_t max_count, uint32_t initial_count)
{
    if (sem == NULL) {
        return OSAL_ERROR;
    }
    sem->max_count = max_count;
    sem->count = initial_count;
    return OSAL_OK;
}''',
            'semaphore_take_nonrtos': '''OSAL_Status_t OSAL_Semaphore_Take(OSAL_Semaphore_t *sem, uint32_t timeout_ms)
{
    (void)timeout_ms;
    if (sem == NULL) {
        return OSAL_ERROR;
    }
    if (sem->count == 0) {
        return OSAL_BUSY;
    }
    sem->count--;
    return OSAL_OK;
}''',
            'semaphore_give_nonrtos': '''OSAL_Status_t OSAL_Semaphore_Give(OSAL_Semaphore_t *sem)
{
    if (sem == NULL) {
        return OSAL_ERROR;
    }
    if (sem->count >= sem->max_count) {
        return OSAL_BUSY;
    }
    sem->count++;
    return OSAL_OK;
}''',
            
            # NonRTOS キュー実装
            'queue_create_nonrtos': '''OSAL_Status_t OSAL_Queue_Create(OSAL_Queue_t *queue, void *buffer, uint32_t size, uint32_t item_size)
{
    if (queue == NULL || buffer == NULL) {
        return OSAL_ERROR;
    }
    queue->buffer = buffer;
    queue->size = size;
    queue->item_size = item_size;
    queue->head = 0;
    queue->tail = 0;
    queue->count = 0;
    return OSAL_OK;
}''',
            'queue_send_nonrtos': '''OSAL_Status_t OSAL_Queue_Send(OSAL_Queue_t *queue, const void *item, uint32_t timeout_ms)
{
    (void)timeout_ms;
    if (queue == NULL || item == NULL) {
        return OSAL_ERROR;
    }
    if (queue->count >= queue->size) {
        return OSAL_BUSY;
    }
    uint8_t *dest = (uint8_t *)queue->buffer + (queue->tail * queue->item_size);
    const uint8_t *src = (const uint8_t *)item;
    for (uint32_t i = 0; i < queue->item_size; i++) {
        dest[i] = src[i];
    }
    queue->tail = (queue->tail + 1) % queue->size;
    queue->count++;
    return OSAL_OK;
}''',
            'queue_receive_nonrtos': '''OSAL_Status_t OSAL_Queue_Receive(OSAL_Queue_t *queue, void *item, uint32_t timeout_ms)
{
    (void)timeout_ms;
    if (queue == NULL || item == NULL) {
        return OSAL_ERROR;
    }
    if (queue->count == 0) {
        return OSAL_BUSY;
    }
    uint8_t *src = (uint8_t *)queue->buffer + (queue->head * queue->item_size);
    uint8_t *dest = (uint8_t *)item;
    for (uint32_t i = 0; i < queue->item_size; i++) {
        dest[i] = src[i];
    }
    queue->head = (queue->head + 1) % queue->size;
    queue->count--;
    return OSAL_OK;
}''',
            
            # NonRTOS クリティカルセクション
            'critical_enter_nonrtos': '''void OSAL_Critical_Enter(void)
{
    /* NonRTOSでは割り込み禁止 */
    __disable_irq();
}''',
            'critical_exit_nonrtos': '''void OSAL_Critical_Exit(void)
{
    /* 割り込み許可 */
    __enable_irq();
}''',
        },
    }