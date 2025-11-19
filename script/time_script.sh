#!/bin/bash

cd ..

export OMP_PROC_BIND=close    # thread pinning su core adiacenti
export OMP_PLACES=cores        # binding a core fisici
export OMP_WAIT_POLICY=active  # evita context switching costoso

data_dir_path="./data"
time_simulation_results="results/final_results_time.csv"

thread_options=(1 2 4 8 16 32 64)
chunk_sizes_options=(1 10 100 1000 10000)
scheduling_options=("static" "dynamic" "guided")
perf_start_options=("C" "W")
src_files=("./src/main.c" "./src/csr.c" "./src/print.c" "./src/mmio.c")

# Estrai info matrici
declare -a input_matrices=()
for f in "$data_dir_path"/*.mtx; do
    while read -r line; do
        if [[ $line != %* ]]; then
            read -r M N nz <<< "$line"
            input_matrices+=("$f,$M,$N,$nz")
            break
        fi
    done < "$f"
done


# Csv header for time results
echo "matrix_name,rows,cols,nz,compiler_option,thread_option,chunk_size_option,scheduling_option,exec_time" > "$time_simulation_results"

# Sequential simulation
echo "starting sequential simulation..."
gcc -g -Iinclude -O3 "${src_files[@]}" -o main
    for matrix_info in "${input_matrices[@]}"; do
        IFS=',' read -r matrix_file M N nz <<< "$matrix_info"
        matrix_name=$(basename "$matrix_file")
        outputs=$(./main "W" "$matrix_file")
        while read -r exec_time; do
            echo "$matrix_name,$M,$N,$nz,-O3,Nan,Nan,Nan,$exec_time" >> "$time_simulation_results"
        done <<< "$outputs"
    done
echo "done."

# Parallel simulation
echo "starting parallel simulation..."
gcc -fopenmp -g -O3 -Iinclude "${src_files[@]}" -o main
for matrix_info in "${input_matrices[@]}"; do
    IFS=',' read -r matrix_file M N nz <<< "$matrix_info"
    matrix_name=$(basename "$matrix_file")
    for to in "${thread_options[@]}"; do
        for cso in "${chunk_sizes_options[@]}"; do
            for so in "${scheduling_options[@]}"; do
                outputs=$(./main "W" "$matrix_file" "$to" "$so" "$cso")
                while read -r exec_time; do
                    echo "$matrix_name,$M,$N,$nz,-O3,$to,$cso,$so,$exec_time" >> "$time_simulation_results"
                done <<< "$outputs"
            done
        done
    done
done
echo "done."