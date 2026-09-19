/**
 * @file    osal.h
 * @brief   OSAL（OS抽象化レイヤ）- NonRTOS
 */
#ifndef OSAL_H
#define OSAL_H

#include <stdint.h>
#include <stdbool.h>

/* OSAL型定義 */
typedef enum {
    OSAL_OK = 0,
    OSAL_ERROR,
    OSAL_TIMEOUT,
    OSAL_BUSY,
} OSAL_Status_t;

typedef struct {
    volatile bool locked;
} OSAL_Mutex_t;

typedef struct {
    volatile uint32_t count;
    volatile uint32_t max_count;
} OSAL_Semaphore_t;

typedef struct {
    void *buffer;
    uint32_t size;
    uint32_t item_size;
    volatile uint32_t head;
    volatile uint32_t tail;
    volatile uint32_t count;
} OSAL_Queue_t;

OSAL_Status_t OSAL_Mutex_Create(OSAL_Mutex_t *mutex);
OSAL_Status_t OSAL_Mutex_Lock(OSAL_Mutex_t *mutex, uint32_t timeout_ms);
OSAL_Status_t OSAL_Mutex_Unlock(OSAL_Mutex_t *mutex);

OSAL_Status_t OSAL_Semaphore_Create(OSAL_Semaphore_t *sem, uint32_t max_count, uint32_t initial_count);
OSAL_Status_t OSAL_Semaphore_Take(OSAL_Semaphore_t *sem, uint32_t timeout_ms);
OSAL_Status_t OSAL_Semaphore_Give(OSAL_Semaphore_t *sem);

OSAL_Status_t OSAL_Queue_Create(OSAL_Queue_t *queue, void *buffer, uint32_t size, uint32_t item_size);
OSAL_Status_t OSAL_Queue_Send(OSAL_Queue_t *queue, const void *item, uint32_t timeout_ms);
OSAL_Status_t OSAL_Queue_Receive(OSAL_Queue_t *queue, void *item, uint32_t timeout_ms);

void OSAL_Critical_Enter(void);
void OSAL_Critical_Exit(void);

#endif /* OSAL_H */