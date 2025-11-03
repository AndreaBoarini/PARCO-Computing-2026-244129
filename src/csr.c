#include "csr.h"

int* COOtoCSR(int *I, int *J, double *val, int nz, int n_rows) {

    int i, j, temp_vec;
    double temp_val;
    int* output_row_ptr = calloc((n_rows + 1), sizeof(int));

    // prepare the COO arrays by sorting them
    for(i = 0; i < nz; i++) {
        for(j = i + 1; j < nz; j++) {
            if(I[i] > I[j] || (I[i] == I[j] && J[i] > J[j])) {
                temp_vec = I[i];
                I[i] = I[j];
                I[j] = temp_vec;
                temp_vec = J[i];
                J[i] = J[j];
                J[j] = temp_vec;
                temp_val = val[i];
                val[i] = val[j];
                val[j] = temp_val;
            }
        }
    }

    // execute the conversion
    // count the number of elements in each row (result shifted by 1)
    for(i = 0; i < nz; i++) {
        output_row_ptr[I[i]]++;
    }

    // apply the prefix-sum
    for(i = 0; i < n_rows; i++) {
        output_row_ptr[i+1] += output_row_ptr[i];
    }

    return output_row_ptr;
}