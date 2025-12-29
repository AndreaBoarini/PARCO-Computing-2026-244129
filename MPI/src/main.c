#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include "mmio.h"

typedef struct {
    double *val;    
    int *local_row_idx;
    int *local_col_idx;
    int local_nz;
} LocalCOO;

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

    int N, M, nz;
    int *send_counts = NULL;
    int *displs = NULL;
    int *send_rows = NULL, *send_cols = NULL;
    double *send_vals = NULL;
    GlobalCOO *mtx = NULL;

    if(rank == 0) {
        const char* matrix_file = argv[1];
        // only rank 0 reads the matrix
        mtx = malloc(sizeof(GlobalCOO));

        // Read the matrix in COO format
        if(mm_read_unsymmetric_sparse(matrix_file, &M, &N, &nz, &mtx->val, &mtx->row_idx, &mtx->col_idx) != 0) {
            fprintf(stderr, "Error reading matrix file %s\n", matrix_file);
            MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
        }

        printf("Matrix read successfully: %d x %d with %d non-zeros\n", M, N, nz);
    }

    // broadcast matrix dimensions to all processes
    MPI_Bcast(&M, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&N, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(&nz, 1, MPI_INT, 0, MPI_COMM_WORLD);

    if(rank == 0) {
        // prepare data for scattering
        send_counts = calloc(size, sizeof(int));
        displs = calloc(size, sizeof(int));

        // count the nnz per rank (ownership by row)
        int i, dest;
        for(i = 0; i < nz; i++) {
            dest = mtx->row_idx[i] % size;
            send_counts[dest]++;
        }

        // calculate displacements
        displs[0] = 0;
        for(i = 1; i < size; i++) {
            displs[i] = displs[i-1] + send_counts[i-1];
        }

        // prepare send buffers
        send_rows = malloc(nz * sizeof(int));
        send_cols = malloc(nz * sizeof(int));
        send_vals = malloc(nz * sizeof(double));

        int *position = malloc(size * sizeof(int));
        for(i = 0; i < size; i++) {
            position[i] = displs[i];
        }
        for(i = 0; i < nz; i++) {
            dest = mtx->row_idx[i] % size;
            int pos = position[dest]++;
            send_rows[pos] = mtx->row_idx[i];
            send_cols[pos] = mtx->col_idx[i];
            send_vals[pos] = mtx->val[i];
        }
        free(position);
    }

    // each rank receives the number of its nnz
    LocalCOO *local_mtx = malloc(sizeof(LocalCOO));
    local_mtx->local_nz = 0;
    MPI_Scatter(send_counts, 1, MPI_INT, &local_mtx->local_nz, 1, MPI_INT, 0, MPI_COMM_WORLD);

    // allocate local arrays
    local_mtx->local_row_idx = malloc(local_mtx->local_nz * sizeof(int));
    local_mtx->local_col_idx = malloc(local_mtx->local_nz * sizeof(int));
    local_mtx->val = malloc(local_mtx->local_nz * sizeof(double));

    // tuple distribution
    // distribute row indices
    MPI_Scatterv(send_rows, send_counts, displs, MPI_INT,
                 local_mtx->local_row_idx, local_mtx->local_nz, MPI_INT,
                 0, MPI_COMM_WORLD);
    // distribute column indices
    MPI_Scatterv(send_cols, send_counts, displs, MPI_INT,
                 local_mtx->local_col_idx, local_mtx->local_nz, MPI_INT,
                 0, MPI_COMM_WORLD);
    // distribute values
    MPI_Scatterv(send_vals, send_counts, displs, MPI_DOUBLE,
                 local_mtx->val, local_mtx->local_nz, MPI_DOUBLE,
                 0, MPI_COMM_WORLD);

    printf("Hello from rank %d / %d\n", rank, size);
    // printf("Broadcast worked fine!: \n M = %d, N = %d, nz = %d\n", M, N, nz);
    // printf("My non-zeros are: %d\n", local_mtx->local_nz);

    // printf("Hi!, I'm rank %d of %d.\n", rank, size);
    // printf("The arrays I stored are:\n");
    for(int i = 0; i < local_mtx->local_nz; i++) {
        printf("%f ", local_mtx->val[i]);
    }
    printf("\n");

    MPI_Finalize();
    return EXIT_SUCCESS;
}