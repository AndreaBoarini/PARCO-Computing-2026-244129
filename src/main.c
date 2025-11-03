#include <stdio.h>
#include <stdlib.h>
#include "timer.h"
#include "mmio.h"
#include "print.h"

int* COOtoCSR(int *I, int *J, double *val, int nz, int n_rows) {

    int i, j, temp_vec;
    double temp_val;
    int* output_row_ptr = calloc((n_rows + 1), sizeof(int));

    // prepare the COO arrays by sorting them
    for(i = 0; i < nz; i++) {
        for(j = i + 1; j < nz; j++) {
            if(I[i] > I[j] || (I[i] == I[j] && J[i] > J[j])) {
                temp_vec = I[i];
                I[i] = I[j];
                I[j] = temp_vec;
                temp_vec = J[i];
                J[i] = J[j];
                J[j] = temp_vec;
                temp_val = val[i];
                val[i] = val[j];
                val[j] = temp_val;
            }
        }
    }

    // execute the conversion
    // count the number of elements in each row (result shifted by 1)
    for(i = 0; i < nz; i++) {
        output_row_ptr[I[i]]++;
    }

    // apply the prefix-sum
    for(i = 0; i < n_rows; i++) {
        output_row_ptr[i+1] += output_row_ptr[i];
    }

    return output_row_ptr;
}

int main() {
    
    FILE *f;
    MM_typecode matcode;
    int M, N, nz = 1;
    int *I, *J, i, *row_ptr = NULL;
    double *val;

    srand(time(NULL));

    // read mtx file from matrix market
    f = fopen("data/slide_matrix.mtx", "r");
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

    printMatrixInCoo(I, J, val, nz);
    row_ptr = COOtoCSR(I, J, val, nz, M);
    printMatrixInCSR(row_ptr, J, val, nz, M);

    // generate a random vector of size N (columns of the matrix)
    double max = 4.0, min = -4.0, range, div;
    range = max - min;
    div = RAND_MAX / range;
    double *vec = malloc(N * sizeof(double));
    for (i = 0; i < N; i++) {
        vec[i] = min + (rand() / div);
    }

    for(i = 0; i < N; i++) {
        printf("%0.2g ", vec[i]);
    }

    // compute the matrix-vector product
    double start_prod, finish_prod;
    double *result = calloc(M, sizeof(double));
    GET_TIME(start_prod);
    for(int i = 0; i < M; i++) {
        for(int j = row_ptr[i]; j < row_ptr[i+1]; j++) {
            result[i] += val[j] * vec[J[j]-1]; // -1 for 0-based indexing
        }
    }
    GET_TIME(finish_prod);
    double elapsed_prod = finish_prod - start_prod;
    printf("\nElapsed time for matrix-vector product: %f\n", elapsed_prod);

    printf("\nResult:\n");
    for(i = 0; i < M; i++) {
        printf("%0.2g ", result[i]);
    }
    printf("\n");

    free(I);
    free(J);
    free(val);
    free(row_ptr);
    free(vec);
    free(result);

    return 0;
}