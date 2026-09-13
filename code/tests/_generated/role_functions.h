/**
 * @brief  ロール関数: StartOk
 * @note   開始条件チェック
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Driver_StartOk(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: LogStop
 * @note   停止ログ
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Driver_LogStop(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: LogError
 * @note   エラーログ
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Driver_LogError(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx
);

/**
 * @brief  ロール関数: Fallback
 * @note   フォールバック処理
 * @param  transition  遷移コンテキスト（NULL 可: ISR から呼ばれる場合）
 * @param  ctx         システムコンテキストポインタ
 * @return 0: 成功, 0以外: エラー（条件判定にも使用可）
 */
int RoleFunc_Driver_Fallback(
    const TransitionContext_Driver_t *transition,
    SystemContext_t *ctx
);

