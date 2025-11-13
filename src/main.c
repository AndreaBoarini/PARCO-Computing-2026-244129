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

    bool perf_cold_start;

    // argument inputs check
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
        if(argc < 6 || argc > 6) {
            fprintf(stderr, "Usage: %s <perf_cold_start> | <mtx_file> <num_of_threads> <schedule_type> <chunk_size> \n", argv[0]);
            exit(EXIT_FAILURE);
        } else {
            num_of_threads = strtol(argv[3], NULL, 10);
            chunk_size = strtol(argv[5], NULL, 10);
            //printf("num_of_threads: %ld, chunk_size: %ld\n", num_of_threads, chunk_size);
            if (strcmp(argv[4], "static") == 0) {
                schedule_type = omp_sched_static;
                //printf("schedule_type: %d\n", schedule_type);
            } else if (strcmp(argv[4], "dynamic") == 0) {
                schedule_type = omp_sched_dynamic;
                //printf("schedule_type: %d\n", schedule_type);
            } else if (strcmp(argv[4], "guided") == 0) {
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
        if(argc != 3) {
            fprintf(stderr, "Too many/few arguments. Usage: %s <perf_cold_start> | <mtx_file>\n", argv[0]);
            exit(EXIT_FAILURE);
        }
        #endif

        if(strcmp(argv[1], "C") == 0) {
            perf_cold_start = true;
        } else if (strcmp(argv[1], "W") == 0) {
            perf_cold_start = false;
        } else {
            fprintf(stderr, "Unknown perf_cold_start value. Use 'C' or 'W'.\n");
            fprintf(stderr, "Usage: %s <perf_cold_start> | <mtx_file> <num_of_threads> <schedule_type> <chunk_size> \n", argv[0]);
            exit(EXIT_FAILURE);
        }
        
    }
    
    srand(time(NULL));
    MM_typecode matcode;
    int M, N, nz = 1;
    int *I, *J, i, *row_ptr = NULL;
    double *val;

    // read mtx file from matrix market format
    readMtx(argv[2], &I, &J, &val, &nz, &M, &N);

    row_ptr = COOtoCSR(I, J, val, nz, M);

    // generate a random vector of size N (columns of the matrix)
    double max = 4.0, min = -4.0, range, div;
    range = max - min;
    div = RAND_MAX / range;
    double *vec = malloc(N * sizeof(double));
    for (i = 0; i < N; i++) {
        vec[i] = min + (rand() / div);
    }

    // compute the matrix-vector product
    double start_time, finish_time, elapsed_time;
    int j, iterations, limit;
    if(perf_cold_start)
        limit = 1;
    else
        limit = 10;        
    double *result = calloc(M, sizeof(double));
    for(iterations = 0; iterations < limit; iterations++) {
        GET_TIME(start_time);

        #pragma omp parallel for schedule(runtime)
        for(i = 0; i < M; i++) {
            double sum = 0.0;
            for(j = row_ptr[i]; j < row_ptr[i+1]; j++) {
                sum += val[j] * vec[J[j]-1]; // -1 for 0-based indexing
            }
            result[i] = sum;
        }

        GET_TIME(finish_time);
        elapsed_time = finish_time - start_time;
        elapsed_time *= 1000;
        printf("%f\n", elapsed_time);
    }

    free(I);
    free(J);
    free(val);
    free(row_ptr);
    free(vec);
    free(result);

    return 0;
}