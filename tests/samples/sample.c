/* Deepwick sample: preprocessor, macros, structs, and labels. */
#include <stdio.h>
#define MAX_RETRIES 3
#define SQUARE(x) ((x) * (x))

struct point {
    int x;
    int y;
};

int main(void) {
    struct point p = {SQUARE(2), MAX_RETRIES};
#ifdef DEBUG
    printf("debug build\n");
#endif
    if (p.x > p.y) {
        goto done;
    }
    printf("point: %d, %d\n", p.x, p.y);
done:
    return 0;
}
