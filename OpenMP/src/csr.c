#include <stdlib.h>
#include "csr.h"
#include "mmio.h"

typedef struct {
    int row;
    int col;
    double value;
} coo_instance;

// define the sorting logic
int compare_coo_instances(const void *a, const void *b) {
    coo_instance *inst_a = (coo_instance *)a;
    coo_instance *inst_b = (coo_instance *)b;

    if (inst_a->row != inst_b->row) {
        return inst_a->row - inst_b->row;
    } else {
        return inst_a->col - inst_b->col;
    }
}

void readMtx(char* filename, int **I, int **J, double **val, int *nz, int *M, int *N) {
    FILE *f;
    MM_typecode matcode;
    int i;

    f = fopen(filename, "r");
    if(f == NULL){
        printf("Error opening file\n");
        exit(-1);
    }
    mm_read_banner(f, &matcode);
    mm_read_mtx_crd_size(f, M, N, nz);

    *I = malloc((*nz) * sizeof(int));
    *J = malloc((*nz) * sizeof(int));
    *val = malloc((*nz) * sizeof(double));

    for (i = 0; i < *nz; i++) {
        fscanf(f, "%d %d %lg\n", &(*I)[i], &(*J)[i], &(*val)[i]);
    }

    fclose(f);
}

int* COOtoCSR(int *I, int *J, double *val, int nz, int n_rows) {

    int i, j, temp_vec;
    double temp_val;
    int* output_row_ptr = calloc((n_rows + 1), sizeof(int));
    coo_instance* coo_array = malloc(nz * sizeof(coo_instance));
    if(coo_array == NULL || output_row_ptr == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }

    // switch to coo_instance structure
    for(i = 0; i < nz; i++) {
        coo_array[i].row = I[i];
        coo_array[i].col = J[i];
        coo_array[i].value = val[i];
    }

    qsort(coo_array, nz, sizeof(coo_instance), compare_coo_instances);

    // reconstrucrt the original arrays once sorted
    for(i = 0; i < nz; i++) {
        I[i] = coo_array[i].row;
        J[i] = coo_array[i].col;
        val[i] = coo_array[i].value;
    }
    free(coo_array);

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