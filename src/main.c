#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include "timer.h"
#include "mmio.h"
#include "print.h"
#include "csr.h"

int main(int argc, char *argv[]) {
    
    FILE *f;
    MM_typecode matcode;
    int M, N, nz = 1;
    int *I, *J, i, *row_ptr = NULL;
    double *val;

    srand(time(NULL));

    // read mtx file from matrix market format
    f = fopen(argv[1], "r");
    if(f == NULL){
        printf("Error opening file\n");
        return -1;
    }
    mm_read_banner(f, &matcode);
    mm_read_mtx_crd_size(f, &M, &N, &nz);

    I = malloc(nz * sizeof(int));
    J = malloc(nz * sizeof(int));
    val = malloc(nz * sizeof(double));

    for (i = 0; i < nz; i++) {
        fscanf(f, "%d %d %lg\n", &I[i], &J[i], &val[i]);
    }

    fclose(f);

    // printMatrixInCoo(I, J, val, nz);
    row_ptr = COOtoCSR(I, J, val, nz, M);
    // printMatrixInCSR(row_ptr, J, val, nz, M);

    // generate a random vector of size N (columns of the matrix)
    double max = 4.0, min = -4.0, range, div;
    range = max - min;
    div = RAND_MAX / range;
    double *vec = malloc(N * sizeof(double));
    for (i = 0; i < N; i++) {
        vec[i] = min + (rand() / div);
    }

    printVectorDouble(vec, N, "random_vector");

    // compute the matrix-vector product
    double start_time, finish_time;
    double *result = calloc(M, sizeof(double));
    GET_TIME(start_time);
    for(int i = 0; i < M; i++) {
        for(int j = row_ptr[i]; j < row_ptr[i+1]; j++) {
            result[i] += val[j] * vec[J[j]-1]; // -1 for 0-based indexing
        }
    }
    GET_TIME(finish_time);
    double elapsed_time = finish_time - start_time;
    printf("Elapsed time for matrix-vector product: %f\n", elapsed_time);

    printVectorDouble(result, M, "result_vector");

    free(I);
    free(J);
    free(val);
    free(row_ptr);
    free(vec);
    free(result);

    return 0;
}