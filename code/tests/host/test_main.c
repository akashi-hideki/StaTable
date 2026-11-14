/* L1 host test driver */
#include <stdio.h>
#include <stdint.h>
#include "statable_comm_monitor.h"

static void tx_fn(uint8_t b)
{
    fputc(b, stdout);
    fflush(stdout);
}

int main(void)
{
    comm_monitor_init();
    comm_monitor_set_tx(tx_fn);
    int c;
    while ((c = getchar()) != EOF) {
        comm_monitor_on_rx_byte((uint8_t)c);
        comm_monitor_poll();
    }
    return 0;
}
