#ifndef __GHOST_H__
#define __GHOST_H__
#include <stdio.h>
#include <stdlib.h>
#include "structures.h"

int compare_values(const void *a, const void *b);
int compare_doubles(const void *a, const void *b);
void build_ghost_list(int N, int size, int rank, LocalX *l_x, int *local_row_ptr, int *local_col_idx, int N_local);
void ghost_exchange(int N, int size, int rank, LocalX *l_x, long long int *n_sends, long long int *n_recvs);
void build_local_x(int N, int N_local, int size, int rank, LocalX *l_x, double *merged_local_x);
void remap_column_idx(int N, int size, int rank, int N_local, int *local_col_idx, LocalX *l_x, int local_nz, int *merged_size);
void spmv(int N_local, int *local_row_ptr, int *local_col_idx, double *val, double* merged_local_x, double *local_y);
double percentile90th(double *data, int n);

#endif 