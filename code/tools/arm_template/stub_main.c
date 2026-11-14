/* Minimal main for link verification.
 * The framework's real entry points are provided by the user;
 * this stub only satisfies the linker's reference to `main`.
 */
int main(void)
{
    for (;;) {
    }
    return 0;
}
/* No dynamic memory in embedded target (MISRA C:2012 Rule 21.3).
 * newlib's snprintf can reference _sbrk; provide a failing stub
 * so link succeeds and any actual malloc call returns NULL. */
void *_sbrk(int incr) {
    (void)incr;
    return (void *)-1;
}
