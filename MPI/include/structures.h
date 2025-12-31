#ifndef __STRUCTURES_H__
#define __STRUCTURES_H__

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

typedef struct {
    double *owned_x;
    double *ghost_entries;
    int n_ghost;
    int *ghost_idx;
} LocalX;

typedef struct {
    int i;
    double j;
} Pair;

#endif
