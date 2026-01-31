#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include <stdbool.h>
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

        // printf("Matrix read successfully: %d x %d with %d non-zeros\n", M, N, nz);

        // generate random vector
        random_vec = malloc(N * sizeof(double));
        if(!random_vec) {
            fprintf(stderr, "Error allocating memory for random vector\n");
            MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
        }
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
        if(!send_counts || !displs) MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);

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
        if(!send_rows || !send_cols || !send_vals) MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);

        int *position = malloc(size * sizeof(int));
        if(!position) MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
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
    if(!local_mtx) MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    local_mtx->local_nz = 0;
    MPI_Scatter(send_counts, 1, MPI_INT, &local_mtx->local_nz, 1, MPI_INT, 0, MPI_COMM_WORLD);

    // allocate local arrays for COO representation
    local_mtx->local_row_idx = malloc(local_mtx->local_nz * sizeof(int));
    local_mtx->local_col_idx = malloc(local_mtx->local_nz * sizeof(int));
    local_mtx->val = malloc(local_mtx->local_nz * sizeof(double));
    if(!local_mtx->local_row_idx || !local_mtx->local_col_idx || !local_mtx->val) {
        fprintf(stderr, "[rank %d] Error allocating memory for local matrix\n", rank);
        MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }

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
    if(!local_x) MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    local_x->owned_x = malloc(N_local * sizeof(double));
    if(!local_x->owned_x) MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    int *counts_x = NULL, *displs_x = NULL;
    double *send_x = NULL;

    if(rank == 0) {
        counts_x = calloc(size, sizeof(int));
        displs_x = calloc(size, sizeof(int));
        if(!counts_x || !displs_x) MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);

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
        if(!send_x) MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
        int *position_x = malloc(size * sizeof(int));
        if(!position_x) MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
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

    // distribute chunks of X
    MPI_Scatterv(send_x, counts_x, displs_x, MPI_DOUBLE, local_x->owned_x, N_local, MPI_DOUBLE,
                    0, MPI_COMM_WORLD);

    build_ghost_list(N, size, rank, local_x, local_row_ptr, local_mtx->local_col_idx, N_local);
    
    // build the complete local vector (owned + ghost)
    int merged_size = 0;
    remap_column_idx(N, size, rank, N_local, local_mtx->local_col_idx, local_x, local_mtx->local_nz, &merged_size);
    
    double *merged_local_x = malloc(merged_size * sizeof(double));
    double *local_y = malloc(N_local * sizeof(double));
    if(!merged_local_x || !local_y) MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);

    // load balance information
    // min/max/avg nnz per rank
    int sum_nnz, max_nnz, min_nnz;
    MPI_Reduce(&local_mtx->local_nz, &max_nnz, 1, MPI_INT, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&local_mtx->local_nz, &min_nnz, 1, MPI_INT, MPI_MIN, 0, MPI_COMM_WORLD);
    MPI_Reduce(&local_mtx->local_nz, &sum_nnz, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);

    // memory footprint for each rank
    size_t local_memory_used = (N_local + 1) * sizeof(int) + // row_ptr
                                local_mtx->local_nz * (sizeof(int) + sizeof(double)) + // col_idx + val
                                (N_local + local_x->n_ghost) * sizeof(double) + // owned_x + ghost_entries
                                local_x->n_ghost * sizeof(int) + // ghost_idx
                                N_local * sizeof(double); // local_y
    
    // conversion to KB
    double local_memory_KB = local_memory_used / 1024.0;
    double max_memory_KB, min_memory_KB, sum_memory_KB;
    MPI_Reduce(&local_memory_KB, &sum_memory_KB, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
    MPI_Reduce(&local_memory_KB, &max_memory_KB, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&local_memory_KB, &min_memory_KB, 1, MPI_DOUBLE, MPI_MIN, 0, MPI_COMM_WORLD);
    double avg_memory_KB = sum_memory_KB / size;

    double tot_times[10], exchange_times[10], spmv_times[10];
    bool volume_measured = false;
    long long n_sends, n_recvs, total_exchange = 0.0;
    long long max_exchange = 0.0, min_exchange = 0.0, sum_exchange = 0.0;
    double avg_exchange;

    // execute 10 iterations and take the 90th out of the times
    // this mitigates the negative effect of process allocation
    // across the nodes, which may vary at each run

    for(int iter = 0; iter < 10; iter++) {

        // wait for all processes to reach this point
        MPI_Barrier(MPI_COMM_WORLD);

        double t0 = MPI_Wtime();
        ghost_exchange(N, size, rank, local_x, &n_sends, &n_recvs);
        double t1 = MPI_Wtime();

        build_local_x(N, N_local, size, rank, local_x, merged_local_x);

        // compute the SpMV product
        double t2 = MPI_Wtime();
        spmv(N_local, local_row_ptr, local_mtx->local_col_idx, local_mtx->val, merged_local_x, local_y);
        double t3 = MPI_Wtime();

        double local_exchange = t1 - t0;
        double local_spmv = t3 - t2;
        double local_total = local_exchange + local_spmv;
        
        // for time measurement we consider the rank with highest total time
        // and communicate its specific times (exchange and SpMV) to the root

        // find the maximum total time among all processes and which rank has it
        MaxTimeRank in, out;
        in.rk = rank;
        in.val = local_total;

        // use MPI_MAXLOC to find the maximum time and corresponding rank
        // MPI_DOUBLE_INT defines how to read the structure and what element to compare
        MPI_Reduce(&in, &out, 1, MPI_DOUBLE_INT, MPI_MAXLOC, 0, MPI_COMM_WORLD);
        
        int critical_rank;
        if (rank == 0) critical_rank = out.rk;
        
        // each rank has to know the critical rank that will give its times
        MPI_Bcast(&critical_rank, 1, MPI_INT, 0, MPI_COMM_WORLD);

        // only the critical rank will store the times to send to the root
        // the others will send 0.0
        double send_critical_exch = (rank == critical_rank) ? local_exchange : 0.0;
        double send_critical_spmv = (rank == critical_rank) ? local_spmv : 0.0;
        double send_critical_total = (rank == critical_rank) ? local_total : 0.0;

        // only the root will use them
        double recv_critical_exch = 0.0;
        double recv_critical_spmv = 0.0;
        double recv_critical_total = 0.0;
        
        // send to the root the critical times
        MPI_Reduce(&send_critical_exch, &recv_critical_exch, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
        MPI_Reduce(&send_critical_spmv, &recv_critical_spmv, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
        MPI_Reduce(&send_critical_total, &recv_critical_total, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
        
        // convert times in ms
        recv_critical_exch *= 1000.0;
        recv_critical_spmv *= 1000.0;
        recv_critical_total *= 1000.0;

        if(rank == 0) {
            exchange_times[iter] = recv_critical_exch;
            spmv_times[iter] = recv_critical_spmv;
            tot_times[iter] = recv_critical_total;
        }

        // communication volume measurement (only once)
        // rank 0 will store all the metrics' information
        if(!volume_measured) {
            volume_measured = true;
            total_exchange = n_sends + n_recvs;
            MPI_Reduce(&total_exchange, &max_exchange, 1, MPI_LONG_LONG_INT, MPI_MAX, 0, MPI_COMM_WORLD);
            MPI_Reduce(&total_exchange, &min_exchange, 1, MPI_LONG_LONG_INT, MPI_MIN, 0, MPI_COMM_WORLD);
            MPI_Reduce(&total_exchange, &sum_exchange, 1, MPI_LONG_LONG_INT, MPI_SUM, 0, MPI_COMM_WORLD);
            avg_exchange = sum_exchange / (double) size;
        }
    }

    // extract the 90th percentile of the times
    double p90_exchange = 0.0, p90_spmv = 0.0, p90_total = 0.0;
    if(rank == 0) {
        p90_exchange = percentile90th(exchange_times, 10);
        p90_spmv = percentile90th(spmv_times, 10);
        p90_total = percentile90th(tot_times, 10);
    }

    // exchange volume per rank (only vector's values)

    if(rank == 0) {
        // print times
        printf("%f\n", p90_spmv);
        printf("%f\n", p90_exchange);
        // print communication volume
        printf("%lld\n", max_exchange);
        printf("%lld\n", min_exchange);
        printf("%f\n", avg_exchange);
        // print load balance
        printf("%d\n", max_nnz);
        printf("%d\n", min_nnz);
        printf("%f\n", sum_nnz / (double) size);
        // print memory footprint
        printf("%f\n", max_memory_KB);
        printf("%f\n", min_memory_KB);
        printf("%f\n", avg_memory_KB);
    }

    MPI_Finalize();

    return EXIT_SUCCESS;
}