#include <stdio.h>
#include <stdlib.h>

void readMtx(char* filename, int **I, int **J, double **val, int *nz, int *M, int *N);
int* COOtoCSR(int *I, int *J, double *val, int nz, int n_rows);