/**
 * @brief  TIMER0 割り込みハンドラ
 * @note   タイマ満了時の処理
 * @note   使用ロール関数:
 *         - Driver.Init
 *         - Application.HandleOverflow
 */
void ISR_TIMER0(void)
{

    /* ===== コンテキスト参照（自動生成） ===== */
    SystemContext_t *ctx = &g_ctx;
    (void)ctx;

    /* ===== 入場ログ ===== */
    LOG_DEBUG("Enter ISR: TIMER0");

    /* ===== アクション（自動生成） ===== */
    ctx->data.counter++;
    RoleFunc_Driver_Init(NULL, ctx);
    if (ctx->data.counter > 100) { RoleFunc_Application_HandleOverflow(NULL, ctx); }

    /* ===== ユーザー追加領域 ===== */
    /* [[STABLE_USER_CODE_START:TIMER0]] */
    /* ユーザー追加コードをここに記述 */
    /* [[STABLE_USER_CODE_END:TIMER0]] */

    /* ===== 退場ログ ===== */
    LOG_DEBUG("Exit ISR: TIMER0");
}

/**
 * @brief  UART_RX 割り込みハンドラ
 * @note   UART 受信割り込み
 * @note   使用ロール関数:
 *         - Driver.Rx
 */
void ISR_UARTRX(void)
{

    /* ===== コンテキスト参照（自動生成） ===== */
    SystemContext_t *ctx = &g_ctx;
    (void)ctx;

    /* ===== 入場ログ ===== */
    LOG_DEBUG("Enter ISR: UART_RX");

    /* ===== アクション（自動生成） ===== */
    RoleFunc_Driver_Rx(NULL, ctx);

    /* ===== ユーザー追加領域 ===== */
    /* [[STABLE_USER_CODE_START:UARTRX]] */
    /* ユーザー追加コードをここに記述 */
    /* [[STABLE_USER_CODE_END:UARTRX]] */

    /* ===== 退場ログ ===== */
    LOG_DEBUG("Exit ISR: UART_RX");
}
