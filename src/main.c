#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "timer.h"
#include "mmio.h"
#include "print.h"
#include "csr.h"
#ifdef _OPENMP
#include <omp.h>
#endif

int main(int argc, char *argv[]) {

    if(argc < 2) {
        fprintf(stderr, "Usage: %s <mtx_file> \n", argv[0]);
        exit(EXIT_FAILURE);
    } else {
        // check if omp compiler flag is enabled
        #ifdef _OPENMP
        // define the environment (thread infos, scheduling and chunksize)
        // initialize with default values
        long num_of_threads = 1;
        long chunk_size = 1;
        omp_sched_t schedule_type = omp_sched_static;
        if(argc < 5 || argc > 5) {
            fprintf(stderr, "Usage: %s <mtx_file> <num_of_threads> <schedule_type> <chunk_size>\n", argv[0]);
            exit(EXIT_FAILURE);
        } else {
            num_of_threads = strtol(argv[2], NULL, 10);
            chunk_size = strtol(argv[4], NULL, 10);
            //printf("num_of_threads: %ld, chunk_size: %ld\n", num_of_threads, chunk_size);
            if (strcmp(argv[3], "static") == 0) {
                schedule_type = omp_sched_static;
                //printf("schedule_type: %d\n", schedule_type);
            } else if (strcmp(argv[3], "dynamic") == 0) {
                schedule_type = omp_sched_dynamic;
                //printf("schedule_type: %d\n", schedule_type);
            } else if (strcmp(argv[3], "guided") == 0) {
                schedule_type = omp_sched_guided;
                //printf("schedule_type: %d\n", schedule_type);
            } else {
                fprintf(stderr, "Unknown schedule type. Use 'static', 'dynamic', or 'guided'.\n");
                exit(EXIT_FAILURE);
            }
            omp_set_num_threads(num_of_threads);
            omp_set_schedule(schedule_type, chunk_size);
        }
        #else
        if(argc != 2) {
            fprintf(stderr, "Too many arguments. Usage: %s <mtx_file>\n", argv[0]);
            exit(EXIT_FAILURE);
        }
        #endif
        
    }
    
    srand(time(NULL));
    MM_typecode matcode;
    int M, N, nz = 1;
    int *I, *J, i, *row_ptr = NULL;
    double *val;

    // read mtx file from matrix market format
    readMtx(argv[1], &I, &J, &val, &nz, &M, &N);

    // printMatrixInCoo(I, J, val, nz);
    row_ptr = COOtoCSR(I, J, val, nz, M);
    // printMatrixInCSR(row_ptr, J, val, nz, M);

    // generate a random vector of size N (columns of the matrix)
    double max = 4.0, min = -4.0, range, div;
    range = max - min;
    div = RAND_MAX / range;
    double *vec = malloc(N * sizeof(double));
    for (i = 0; i < N; i++) {
        vec[i] = min + (rand() / div);
    }

    //printVectorDouble(vec, N, "random_vector");

    // compute the matrix-vector product
    double start_time, finish_time;
    int j;
    double *result = calloc(M, sizeof(double));
    GET_TIME(start_time);

    #pragma omp parallel for schedule (runtime)
    for(i = 0; i < M; i++) {
        for(j = row_ptr[i]; j < row_ptr[i+1]; j++) {
            result[i] += val[j] * vec[J[j]-1]; // -1 for 0-based indexing
        }
    }

    GET_TIME(finish_time);
    double elapsed_time = finish_time - start_time;
    elapsed_time *= 1e6;
    //printf("Elapsed time for matrix-vector product (ms): %f\n", elapsed_time);
    printf("%f\n", elapsed_time);

    //printVectorDouble(result, M, "result_vector");

    free(I);
    free(J);
    free(val);
    free(row_ptr);
    free(vec);
    free(result);

    return 0;
}