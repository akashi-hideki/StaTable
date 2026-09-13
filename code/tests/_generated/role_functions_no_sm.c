/**
 * @brief  ロール関数: StartOk
 * @note   開始条件チェック
 *
 * @note   呼び出し元: （なし）
 */
int RoleFunc_Driver_StartOk(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_Driver_t from_state = STATE_Driver_MAX;
    EVENT_Driver_t event = EVENT_Driver_NONE;
    if (transition != NULL) {
        from_state = transition->from_state;
        event = transition->event;
    }
    (void)from_state;   /* 未使用警告抑制 */
    (void)event;   /* 未使用警告抑制 */

    (void)ctx;         /* 未使用引数の警告抑制 */
    /* ===== 戻り値 ===== */
    int ret = 0;   /* ユーザーコード内で書き換え可 */

    /* TODO: 実装を記述すること */

    /* [[STABLE_USER_CODE_START:Driver_StartOk]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:Driver_StartOk]] */

    return ret;
}

/**
 * @brief  ロール関数: LogStop
 * @note   停止ログ
 *
 * @note   呼び出し元: （なし）
 */
int RoleFunc_Driver_LogStop(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_Driver_t from_state = STATE_Driver_MAX;
    EVENT_Driver_t event = EVENT_Driver_NONE;
    if (transition != NULL) {
        from_state = transition->from_state;
        event = transition->event;
    }
    (void)from_state;   /* 未使用警告抑制 */
    (void)event;   /* 未使用警告抑制 */

    (void)ctx;         /* 未使用引数の警告抑制 */
    /* ===== 戻り値 ===== */
    int ret = 0;   /* ユーザーコード内で書き換え可 */

    /* TODO: 実装を記述すること */

    /* [[STABLE_USER_CODE_START:Driver_LogStop]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:Driver_LogStop]] */

    return ret;
}

/**
 * @brief  ロール関数: LogError
 * @note   エラーログ
 *
 * @note   呼び出し元: （なし）
 */
int RoleFunc_Driver_LogError(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_Driver_t from_state = STATE_Driver_MAX;
    EVENT_Driver_t event = EVENT_Driver_NONE;
    if (transition != NULL) {
        from_state = transition->from_state;
        event = transition->event;
    }
    (void)from_state;   /* 未使用警告抑制 */
    (void)event;   /* 未使用警告抑制 */

    (void)ctx;         /* 未使用引数の警告抑制 */
    /* ===== 戻り値 ===== */
    int ret = 0;   /* ユーザーコード内で書き換え可 */

    /* TODO: 実装を記述すること */

    /* [[STABLE_USER_CODE_START:Driver_LogError]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:Driver_LogError]] */

    return ret;
}

/**
 * @brief  ロール関数: Fallback
 * @note   フォールバック処理
 *
 * @note   呼び出し元: （なし）
 */
int RoleFunc_Driver_Fallback(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx
)
{
    /* ===== transition NULL ガード（ISR からの呼び出し対応） ===== */
    STATE_Driver_t from_state = STATE_Driver_MAX;
    EVENT_Driver_t event = EVENT_Driver_NONE;
    if (transition != NULL) {
        from_state = transition->from_state;
        event = transition->event;
    }
    (void)from_state;   /* 未使用警告抑制 */
    (void)event;   /* 未使用警告抑制 */

    (void)ctx;         /* 未使用引数の警告抑制 */
    /* ===== 戻り値 ===== */
    int ret = 0;   /* ユーザーコード内で書き換え可 */

    /* TODO: 実装を記述すること */

    /* [[STABLE_USER_CODE_START:Driver_Fallback]] */
    /* ユーザー実装コードをここに記述 */
    /* [[STABLE_USER_CODE_END:Driver_Fallback]] */

    return ret;
}



/* ============================================================== */
/*  ユーザー追加領域                                              */
/*  ここに追加したコードは再生成時も保持されます                  */
/* ============================================================== */
/* [[STABLE_USER_CODE_TAIL_START]] */
/* ユーザー追加コードをここに記述（ヘルパー関数など） */
/* [[STABLE_USER_CODE_TAIL_END]] */
