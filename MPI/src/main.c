#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include "mmio.h"

typedef struct {      
    double *val;    
    int *row_idx;
    int *col_idx;
} GlobalCOO;

int main(int argc, char* argv[]) {

    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if(argc < 2) {
        if(rank == 0) {
            fprintf(stderr, "Usage: %s <matrix_file>\n", argv[0]);
        }
        MPI_Finalize();
        return EXIT_FAILURE;
    }

    if(rank == 0) {
        const char* matrix_file = argv[1];
        GlobalCOO *mtx = malloc(sizeof(GlobalCOO));
        int N, M, nz;

        // Read the matrix in COO format
        if(mm_read_unsymmetric_sparse(matrix_file, &M, &N, &nz, &mtx->val, &mtx->row_idx, &mtx->col_idx) != 0) {
            fprintf(stderr, "Error reading matrix file %s\n", matrix_file);
            MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
        }

        printf("Matrix read successfully: %d x %d with %d non-zeros\n", M, N, nz);

        // Free allocated memory
        free(mtx->val);
        free(mtx->row_idx);
        free(mtx->col_idx);
        free(mtx);
    }



    MPI_Finalize();
    return EXIT_SUCCESS;
}