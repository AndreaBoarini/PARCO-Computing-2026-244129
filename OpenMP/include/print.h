#ifndef _PRINT_H_
#define _PRINT_H_

void printVectorInt(int *vec, int size, char* tag);
void printVectorDouble(double *vec, int size, char* tag);
void printMatrixIntrinsic(int *I, int *J, double *val, int nz);
void printMatrixInCoo(int *I, int *J, double *val, int nz);
void printMatrixInCSR(int *row_ptr, int *J, double *val, int nz, int n_rows);

#endif
