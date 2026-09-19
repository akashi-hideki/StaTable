/**
 * @file    osal.c
 * @brief   OSAL（OS抽象化レイヤ）- NonRTOS
 */
#include <stdint.h>
#include <stdbool.h>

/* ミューテックス実装 */
OSAL_Status_t OSAL_Mutex_Create(OSAL_Mutex_t *mutex)
{
    if (mutex == NULL) {
        return OSAL_ERROR;
    }
    mutex->locked = false;
    return OSAL_OK;
}

OSAL_Status_t OSAL_Mutex_Lock(OSAL_Mutex_t *mutex, uint32_t timeout_ms)
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
}

OSAL_Status_t OSAL_Mutex_Unlock(OSAL_Mutex_t *mutex)
{
    if (mutex == NULL) {
        return OSAL_ERROR;
    }
    mutex->locked = false;
    return OSAL_OK;
}

/* セマフォ実装 */
OSAL_Status_t OSAL_Semaphore_Create(OSAL_Semaphore_t *sem, uint32_t max_count, uint32_t initial_count)
{
    if (sem == NULL) {
        return OSAL_ERROR;
    }
    sem->max_count = max_count;
    sem->count = initial_count;
    return OSAL_OK;
}

OSAL_Status_t OSAL_Semaphore_Take(OSAL_Semaphore_t *sem, uint32_t timeout_ms)
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
}

OSAL_Status_t OSAL_Semaphore_Give(OSAL_Semaphore_t *sem)
{
    if (sem == NULL) {
        return OSAL_ERROR;
    }
    if (sem->count >= sem->max_count) {
        return OSAL_BUSY;
    }
    sem->count++;
    return OSAL_OK;
}

/* キュー実装 */
OSAL_Status_t OSAL_Queue_Create(OSAL_Queue_t *queue, void *buffer, uint32_t size, uint32_t item_size)
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
}

OSAL_Status_t OSAL_Queue_Send(OSAL_Queue_t *queue, const void *item, uint32_t timeout_ms)
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
}

OSAL_Status_t OSAL_Queue_Receive(OSAL_Queue_t *queue, void *item, uint32_t timeout_ms)
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
}

/* クリティカルセクション実装 */
void OSAL_Critical_Enter(void)
{
    /* NonRTOSでは割り込み禁止 */
    __disable_irq();
}

void OSAL_Critical_Exit(void)
{
    /* 割り込み許可 */
    __enable_irq();
}
