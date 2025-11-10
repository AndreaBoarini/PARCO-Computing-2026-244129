#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[]) {
    
    int a, b = 3;
    int* vec = calloc(10, sizeof(int));
    for (a = 0; a < 10; a++) {
        vec[a] = a;
    }

    for (a = 0; a < 10; a++) {
        vec[a] += b;
    }

    free(vec);

    return 0;
}