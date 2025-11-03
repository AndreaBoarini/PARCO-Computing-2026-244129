#include "print.h"
#include <stdlib.h>
#include <stdio.h>

void printVector(int *vec, int size, char* tag){
    int i;
    printf("%s = [", tag);
    for(i = 0; i < size; i++) {
        printf(" %d ", vec[i]);
    }
    printf("]\n");
}

void printMatrixIntrinsic(int *I, int *J, double *val, int nz) {
    int i;
    for (i = 0; i < nz; i++) {
        printf("(%d, %d) -> %g\n", I[i], J[i], val[i]);
    }
    printf("non-zero elements: %d\n", nz);
}

void printMatrixInCoo(int *I, int *J, double *val, int nz) {
    printVector(I, nz, "row_ind");
    printVector(J, nz, "col_ind");
    int i;
    printf("%s = [", "val");
    for(i = 0; i < nz; i++) {
        printf(" %g ", val[i]);
    }
    printf("]\n");
    printf("non-zero elements: %d\n", nz);
}

void printMatrixInCSR(int *row_ptr, int *J, double *val, int nz, int n_rows) {
    printVector(row_ptr, n_rows + 1, "row_ptr");
    printVector(J, nz, "col_ind");
    int i;
    printf("%s = [", "val");
    for(i = 0; i < nz; i++) {
        printf(" %g ", val[i]);
    }
    printf("]\n");
    printf("non-zero elements: %d\n", nz);
}