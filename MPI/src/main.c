#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include "mmio.h"
#include "csr.h"
#include "ghost.h"
#include "structures.h"

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
    double *random_vec = NULL;
    GlobalCOO *mtx = NULL;
    LocalX *local_x = NULL;

    if(rank == 0) {
        const char* matrix_file = argv[1];
        double max = 4.0, min = -4.0, range, div;
        range = max - min;
        div = RAND_MAX / range;

        // only rank 0 reads the matrix
        mtx = malloc(sizeof(GlobalCOO));

        // Read the matrix in COO format
        if(mm_read_unsymmetric_sparse(matrix_file, &M, &N, &nz, &mtx->val, &mtx->row_idx, &mtx->col_idx) != 0) {
            fprintf(stderr, "Error reading matrix file %s\n", matrix_file);
            MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
        }

        printf("Matrix read successfully: %d x %d with %d non-zeros\n", M, N, nz);

        // generate random vector
        random_vec = malloc(N * sizeof(double));
        for(int i = 0; i < N; i++) {
            random_vec[i] = min + (rand() / div);
            // printf("%f ", random_vec[i]);
        }
        // printf("\n");
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
    MPI_Scatterv(send_rows, send_counts, displs, MPI_INT, local_mtx->local_row_idx, local_mtx->local_nz, MPI_INT,
                    0, MPI_COMM_WORLD);
    // distribute column indices
    MPI_Scatterv(send_cols, send_counts, displs, MPI_INT, local_mtx->local_col_idx, local_mtx->local_nz, MPI_INT,
                    0, MPI_COMM_WORLD);
    // distribute values
    MPI_Scatterv(send_vals, send_counts, displs, MPI_DOUBLE, local_mtx->val, local_mtx->local_nz, MPI_DOUBLE,
                    0, MPI_COMM_WORLD);

    // mapping from global to local row indices
    // the local rows are 'packed' in a remapped matrix
    int max_row = -1;
    int j;
    for(j = 0; j < local_mtx->local_nz; j++) {
        int g = local_mtx->local_row_idx[j];
        if (g % size != rank) {
            fprintf(stderr, "[rank %d] ERROR: global row out of range: %d (M=%d)\n", rank, g, M);
            MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
        }
        if (g < 0 || g >= M) {
            fprintf(stderr, "[rank %d] ERROR: row %d belongs to %d\n", rank, g, g % size);
            MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
        }
        int aux = g / size;
        local_mtx->local_row_idx[j] = aux;  
        if(aux > max_row) {
            max_row = aux;
        }
    }

    int N_local = 0;
    for (int g = rank; g < M; g += size) N_local++;

    for (int j = 0; j < local_mtx->local_nz; j++) {
    int lr = local_mtx->local_row_idx[j];
    if (lr < 0 || lr >= N_local) {
            fprintf(stderr, "[rank %d] ERROR: local row out of range: %d (N_local=%d)\n",
                    rank, lr, N_local);
            MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
        }
    }
    
    // safely convert to CSR format using the new mapping
    int *local_row_ptr = NULL;
    local_row_ptr = COOtoCSR(local_mtx->local_row_idx, local_mtx->local_col_idx, local_mtx->val, local_mtx->local_nz, N_local);
    
    // pack and distribute the local x vector
    local_x = malloc(sizeof(LocalX));
    local_x->owned_x = malloc(N_local * sizeof(double));
    int *counts_x = NULL, *displs_x = NULL;
    double *send_x = NULL;

    if(rank == 0) {
        counts_x = calloc(size, sizeof(int));
        displs_x = calloc(size, sizeof(int));

        // count how many entries each rank will recieve
        for(int j = 0; j < N; j++) {
            counts_x[j % size]++;
        }

        // get displacements
        // same way as before with rows
        displs_x[0] = 0;
        for(int j = 1; j < size; j++) {
            displs_x[j] = displs_x[j-1] + counts_x[j-1];
        }

        // prepare send_x buffer
        send_x = malloc(N * sizeof(double));
        int *position_x = malloc(size * sizeof(int));
        for(int j = 0; j < size; j++) {
            position_x[j] = displs_x[j];
        }
        for(int j = 0; j < N; j++) {
            int dest = j % size;
            int pos = position_x[dest]++;
            send_x[pos] = random_vec[j];
        }

        free(position_x);
    }

    // dsitribute chunks of X
    MPI_Scatterv(send_x, counts_x, displs_x, MPI_DOUBLE, local_x->owned_x, N_local, MPI_DOUBLE,
                    0, MPI_COMM_WORLD);

    build_ghost_list(N, size, rank, local_x);

    ghost_exchange(N, size, rank, local_x);

    // build the complete local vector (owned + ghost)
    double *merged_local_x = calloc(N, sizeof(double));
    build_local_x(N, N_local, size, rank, local_x, merged_local_x);

    // compute the SpMV product
    double *local_y = malloc(N_local * sizeof(double));
    spmv(N_local, local_row_ptr, local_mtx->local_col_idx, local_mtx->val, merged_local_x, local_y);

    MPI_Finalize();
    return EXIT_SUCCESS;
}