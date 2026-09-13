/**
 * @file    statable_event_queue.c
 * @brief   イベントキュー実装
 *
 * @note    StaTableにより自動生成されたコード
 *          - 手動での編集は推奨しない
 *          - 変更する場合はStaTableで行うこと
 *
 * @date    2026-09-13 11:55:41
 */

/*==============================================================*/
 *  インクルードファイル
/*==============================================================*/

#include "statable_types.h"

/*==============================================================*/
 *  型定義
/*==============================================================*/

/* イベントキュー: MainEventQueue */
/* メインイベントキュー */
typedef struct {
    EVENT_t buffer[16];
    uint8_t head;
    uint8_t tail;
    uint8_t count;
    bool interrupt_safe;
} MainEventQueue_t;

/**
 * @brief  イベントをエンキューする（MainEventQueue）
 * @param  queue  キュー
 * @param  event  イベント
 * @return 成功: true, 失敗: false
 */
bool EventQueue_MainEventQueue_Enqueue(MainEventQueue_t *queue, EVENT_t event)
{
    if (queue == NULL) {
        return false;
    }
    if (queue->count >= 16) {
        return false;  /* キュー満杯 */
    }
    queue->buffer[queue->tail] = event;
    queue->tail = (queue->tail + 1) % 16;
    queue->count++;
    return true;
}

/**
 * @brief  イベントをデキューする（MainEventQueue）
 * @param  queue  キュー
 * @param  event  取り出したイベント
 * @return 成功: true, 失敗: false
 */
bool EventQueue_MainEventQueue_Dequeue(MainEventQueue_t *queue, EVENT_t *event)
{
    if (queue == NULL) {
        return false;
    }
    if (queue->count == 0) {
        return false;  /* キュー空 */
    }
    if (event == NULL) {
        return false;
    }
    *event = queue->buffer[queue->head];
    queue->head = (queue->head + 1) % 16;
    queue->count--;
    return true;
}

/* イベントキュー: HighPriorityQueue */
/* 高優先度イベントキュー */
typedef struct {
    EVENT_t buffer[8];
    uint8_t head;
    uint8_t tail;
    uint8_t count;
    bool interrupt_safe;
} HighPriorityQueue_t;

/**
 * @brief  イベントをエンキューする（HighPriorityQueue）
 * @param  queue  キュー
 * @param  event  イベント
 * @return 成功: true, 失敗: false
 */
bool EventQueue_HighPriorityQueue_Enqueue(HighPriorityQueue_t *queue, EVENT_t event)
{
    if (queue == NULL) {
        return false;
    }
    if (queue->count >= 8) {
        return false;  /* キュー満杯 */
    }
    queue->buffer[queue->tail] = event;
    queue->tail = (queue->tail + 1) % 8;
    queue->count++;
    return true;
}

/**
 * @brief  イベントをデキューする（HighPriorityQueue）
 * @param  queue  キュー
 * @param  event  取り出したイベント
 * @return 成功: true, 失敗: false
 */
bool EventQueue_HighPriorityQueue_Dequeue(HighPriorityQueue_t *queue, EVENT_t *event)
{
    if (queue == NULL) {
        return false;
    }
    if (queue->count == 0) {
        return false;  /* キュー空 */
    }
    if (event == NULL) {
        return false;
    }
    *event = queue->buffer[queue->head];
    queue->head = (queue->head + 1) % 8;
    queue->count--;
    return true;
}
