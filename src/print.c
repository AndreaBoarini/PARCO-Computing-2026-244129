#include "print.h"
#include <stdlib.h>
#include <stdio.h>

void printVectorInt(int *vec, int size, char* tag){
    int i;
    printf("%s = [", tag);
    for(i = 0; i < size; i++) {
        printf(" %d ", vec[i]);
    }
    printf("]\n");
}

void printVectorDouble(double *vec, int size, char* tag){
    int i;
    printf("%s = [", tag);
    for(i = 0; i < size; i++) {
        printf(" %0.2f ", vec[i]);
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
    printVectorInt(I, nz, "row_ind");
    printVectorInt(J, nz, "col_ind");
    printVectorDouble(val, nz, "val");
    printf("non-zero elements: %d\n", nz);
}

void printMatrixInCSR(int *row_ptr, int *J, double *val, int nz, int n_rows) {
    printVectorInt(row_ptr, n_rows + 1, "row_ptr");
    printVectorInt(J, nz, "col_ind");
    printVectorDouble(val, nz, "val");
    printf("non-zero elements: %d\n", nz);
}