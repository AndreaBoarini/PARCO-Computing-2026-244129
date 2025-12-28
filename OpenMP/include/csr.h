#ifndef _CSR_H_
#define _CSR_H_

#include <stdio.h>
#include <stdlib.h>

void readMtx(char* filename, int **I, int **J, double **val, int *nz, int *M, int *N);
int* COOtoCSR(int *I, int *J, double *val, int nz, int n_rows);

#endif