# codegen/code_templates.py
"""
コード生成用テンプレート定義
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
        'function_decls': '関数宣言',
        'role_functions': 'ロール関数宣言',
        'role_impl': 'ロール関数実装',
        'transition_table': '状態遷移テーブル',
        'transition_func': '状態遷移関数',
        'init_func': '初期化関数',
        'var_macros': '変数アクセスマクロ',
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
    }
    
    # ===== 列挙型コメント定義 =====
    ENUM_COMMENTS = {
        'state': {'title': '状態定義', 'description': '状態遷移の状態を表す列挙型'},
        'event': {'title': 'イベント定義', 'description': '状態遷移を発生させるイベントの列挙型'},
        'flag': {'title': 'イベントフラグ定義', 'description': 'イベントフラグの識別子を表す列挙型'},
    }
    
    # ===== 関数コメント定義 =====
    FUNCTION_COMMENTS = {
        'state_machine_process': {
            'brief': '状態遷移処理',
            'params': [
                ('current_state', '現在の状態'),
                ('event', '発生したイベント'),
                ('ctx', 'システムコンテキストポインタ'),
            ],
            'return': '遷移後の状態',
        },
        'system_context_init': {
            'brief': 'システムコンテキスト初期化',
            'params': [('ctx', 'システムコンテキストポインタ')],
            'return': None,
        },
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
    }
    
    # ===== 関数名定義 =====
    FUNCTION_NAMES = {
        'state_machine_process': 'StateMachine_Process',
        'system_context_init': 'SystemContext_Init',
        'role_func_prefix': 'RoleFunc',
        'action_prefix': 'Action',
        'condition_prefix': 'Condition',
    }
    
    # ===== マクロ名定義 =====
    MACRO_NAMES = {
        'data_prefix': 'DATA_',
        'flag_prefix': 'FLAG_',
        'max_suffix': '_MAX',
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
    }
    
    # ===== OSAL関連テンプレート =====
    OSAL = {
        # OS種別定義
        'os_types': {
            'non_rtos': {
                'name': 'NonRTOS',
                'description': 'RTOSなし（ベアメタル）',
                'header': 'osal.h',
                'source': 'osal.c',
            },
            'freertos': {
                'name': 'FreeRTOS',
                'description': 'FreeRTOS',
                'header': 'osal_freertos.h',
                'source': 'osal_freertos.c',
            },
            'threadx': {
                'name': 'ThreadX',
                'description': 'Azure RTOS ThreadX',
                'header': 'osal_threadx.h',
                'source': 'osal_threadx.c',
            },
        },
        
        # ヘッダファイルテンプレート
        'header': {
            'file_comment': '''/**
 * @file    {filename}
 * @brief   OSAL（OS抽象化レイヤ）- {os_name}
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
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
            'mutex_type_nonrtos': '''/* ミューテックス型 */
typedef struct {
    volatile bool locked;
} OSAL_Mutex_t;''',
            'semaphore_type_nonrtos': '''/* セマフォ型 */
typedef struct {
    volatile uint32_t count;
    volatile uint32_t max_count;
} OSAL_Semaphore_t;''',
            'queue_type_nonrtos': '''/* キュー型 */
typedef struct {
    void *buffer;
    uint32_t size;
    uint32_t item_size;
    volatile uint32_t head;
    volatile uint32_t tail;
    volatile uint32_t count;
} OSAL_Queue_t;''',
            'mutex_decls': '''/* ミューテックス関数 */
OSAL_Status_t OSAL_Mutex_Create(OSAL_Mutex_t *mutex);
OSAL_Status_t OSAL_Mutex_Lock(OSAL_Mutex_t *mutex, uint32_t timeout_ms);
OSAL_Status_t OSAL_Mutex_Unlock(OSAL_Mutex_t *mutex);''',
            'semaphore_decls': '''/* セマフォ関数 */
OSAL_Status_t OSAL_Semaphore_Create(OSAL_Semaphore_t *sem, uint32_t max_count, uint32_t initial_count);
OSAL_Status_t OSAL_Semaphore_Take(OSAL_Semaphore_t *sem, uint32_t timeout_ms);
OSAL_Status_t OSAL_Semaphore_Give(OSAL_Semaphore_t *sem);''',
            'queue_decls': '''/* キュー関数 */
OSAL_Status_t OSAL_Queue_Create(OSAL_Queue_t *queue, void *buffer, uint32_t size, uint32_t item_size);
OSAL_Status_t OSAL_Queue_Send(OSAL_Queue_t *queue, const void *item, uint32_t timeout_ms);
OSAL_Status_t OSAL_Queue_Receive(OSAL_Queue_t *queue, void *item, uint32_t timeout_ms);''',
            'critical_decls': '''/* クリティカルセクション関数 */
void OSAL_Critical_Enter(void);
void OSAL_Critical_Exit(void);''',
            'freertos_includes': '''/* FreeRTOSヘッダ */
#include "FreeRTOS.h"
#include "semphr.h"
#include "queue.h"''',
            'threadx_includes': '''/* ThreadXヘッダ */
#include "tx_api.h"''',
        },
        
        # ソースファイルテンプレート
        'source': {
            'file_comment': '''/**
 * @file    {filename}
 * @brief   OSAL（OS抽象化レイヤ）- {os_name} 実装
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
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