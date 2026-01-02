#include "ghost.h"
#include <stdbool.h>
#include <mpi.h>

int compare_values(const void *a, const void *b) {
    int x = ((const Pair *)a)->i;
    int y = ((const Pair *)b)->i;
    return (x > y) - (x < y);
}

void build_ghost_list(int N, int size, int rank, LocalX *l_x) {

    int n_ghost = 0, aux = 0;
    bool *is_ghost = calloc(N, sizeof(bool));

    // create the ghost mask (N = M = dimension of X)
    for(int i = 0; i < N; i++) {
        if(i % size != rank) is_ghost[i] = true;
    }

    // count ghost entries
    for(int i = 0; i < N; i++) {
        if(is_ghost[i]) n_ghost++;
    }

    l_x->n_ghost = n_ghost;
    l_x->ghost_entries = malloc(n_ghost * sizeof(double));
    l_x->ghost_idx = malloc(n_ghost * sizeof(int));

    // fill ghost entries
    for(int i = 0; i < N; i++) {
        if(is_ghost[i]) l_x->ghost_idx[aux++] = i;
    }

    // deallocate ghost mask
    free(is_ghost);
}

void ghost_exchange(int N, int size, int rank, LocalX *l_x) {
    
    int *send_counts = calloc(size, sizeof(int));
    int *recv_counts = calloc(size, sizeof(int));
    int *send_displs = calloc(size, sizeof(int));
    int *recv_displs = calloc(size, sizeof(int));
    int send_tot, recv_tot;

    // group ghost entries by owner
    for(int i = 0; i < l_x->n_ghost; i++) {
        int owner = l_x->ghost_idx[i] % size;
        send_counts[owner]++;
    }

    // excahnge how many entries will be send/received 
    MPI_Alltoall(send_counts, 1, MPI_INT, recv_counts, 1, MPI_INT, MPI_COMM_WORLD);

    // calculate displacements (same logic as everywhere else)
    send_displs[0] = 0;
    recv_displs[0] = 0;
    for(int i = 1; i < size; i++) {
        send_displs[i] = send_displs[i-1] + send_counts[i-1];
        recv_displs[i] = recv_displs[i-1] + recv_counts[i-1];
    }

    send_tot = send_displs[size-1] + send_counts[size-1];
    recv_tot = recv_displs[size-1] + recv_counts[size-1];

    // prepare send buffer
    int *send_idx = malloc(send_tot * sizeof(int));
    int *position = malloc(size * sizeof(int));
    for(int i = 0; i < size; i++) {
        position[i] = send_displs[i];
    }

    for(int i = 0; i < l_x->n_ghost; i++) {
        int owner = l_x->ghost_idx[i] % size;
        int pos = position[owner]++;
        send_idx[pos] = l_x->ghost_idx[i];
    }

    // exchange the lists of the requested elements by each rank
    int *recv_idx = malloc(recv_tot * sizeof(int));
    MPI_Alltoallv(send_idx, send_counts, send_displs, MPI_INT, recv_idx, recv_counts, recv_displs, MPI_INT,
                  MPI_COMM_WORLD);

    // prepare the responses to the requests
    // note that each element in recv_idx belongs to this rank
    double *send_vals = malloc(recv_tot * sizeof(double));
    for(int i = 0; i < recv_tot; i++) {
        send_vals[i] = l_x->owned_x[recv_idx[i] / size];
    }

    // actual exchange of the requested values
    // note that recv_vals is allined with send_idx
    // it needs to be inserted into l_x->ghost_entries respecting the order of l_x->ghost_idx
    double *recv_vals = malloc(send_tot * sizeof(double));
    MPI_Alltoallv(send_vals, recv_counts, recv_displs, MPI_DOUBLE, recv_vals, send_counts, send_displs, MPI_DOUBLE,
                  MPI_COMM_WORLD);

    // sorting is also needed to execute a faster lookup for the SpMV step
    Pair *p = malloc(send_tot * sizeof(Pair));
    qsort(p, send_tot, sizeof(Pair), compare_values);

    for(int i = 0; i < send_tot; i++) {
        p[i].i = send_idx[i];
        p[i].j = recv_vals[i];
    }

    int pair_idx = 0;
    for(int i = 0; i < l_x->n_ghost; i++) {
        int idx = l_x->ghost_idx[i];
        while(p[pair_idx].i != idx) pair_idx++;
        l_x->ghost_entries[i] = p[pair_idx].j;
    }

    free(position);
    free(send_counts);
    free(recv_counts);
    free(send_displs);
    free(recv_displs);
    free(send_idx);
    free(recv_idx);
    free(send_vals);
    free(recv_vals);
    free(p);
}

void build_local_x(int N, int N_local, int size, int rank, LocalX *l_x, double *merged_local_x) {
    
    int aux;

    // insert owned entries
    for(int i = 0; i < N_local; i++) {
        aux = rank + i * size;
        if(aux >= N) break;
        merged_local_x[aux] = l_x->owned_x[i];
    }

    if(l_x->n_ghost > 0) {
        // insert ghost entries
        for(int i = 0; i < l_x->n_ghost; i++) {
            aux = l_x->ghost_idx[i];
            merged_local_x[aux] = l_x->ghost_entries[i];
        }
    }
}

void spmv(int N_local, int *local_row_ptr, int *local_col_idx, double *val, double *merged_local_x, double *local_y) {
    
    int col;
    double sum, value, factor;

    for(int i = 0; i < N_local; i++) {
        sum = 0.0;
        for(int j = local_row_ptr[i]; j < local_row_ptr[i+1]; j++) {
            sum += val[j] * merged_local_x[local_col_idx[j]];
        }
        local_y[i] = sum;
    }
}