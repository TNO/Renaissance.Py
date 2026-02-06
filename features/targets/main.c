#include <stdio.h>

static int static_int = 2;

#define A_DEFINE (4 + static_int)
#define B_DEFINE (A_DEFINE + static_int)

#define FC_MACRO(arg)\
do{\
   arg += A_DEFINE;\
} while(0)

int main() {
    int qwerty = 3 + A_DEFINE;
    FC_MACRO(qwerty);
    printf("QWERTY %d", qwerty+static_int);
    FC_MACRO(qwerty);
    return 0;
}