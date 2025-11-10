#!/bin/bash

data_dir_path="./data"
time_simulation_results="time_results.csv"

compiler_options=("-O0" "-O1" "-O2" "-O3")
thread_options=(1 2 4 8)
chunk_sizes_options=(1 10 100 1000)
scheduling_options=("static" "dynamic" "guided")
src_files=("src/main.c" "src/csr.c" "src/print.c" "src/mmio.c")

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

# Crea CSV intestazioni
echo "matrix_name,rows,cols,nz,compiler_option,thread_option,chunk_size_option,scheduling_option,exec_time" > "$time_simulation_results"

# SEQUENZIALE
echo "starting sequential simulation..."
for co in "${compiler_options[@]}"; do
    gcc -g -Iinclude "${src_files[@]}" "$co" -o main
    for matrix_info in "${input_matrices[@]}"; do
        IFS=',' read -r matrix_file M N nz <<< "$matrix_info"
        matrix_name=$(basename "$matrix_file")
        for i in {1..10}; do
            exec_time=$(./main "$matrix_file")
            echo "$matrix_name,$M,$N,$nz,$co,Nan,Nan,Nan,$exec_time" >> "$time_simulation_results"
        done
    done
done
echo "done."

# PARALLELO
echo "starting parallel simulation..."
gcc -fopenmp -g -Iinclude "${src_files[@]}" -o main
for matrix_info in "${input_matrices[@]}"; do
    IFS=',' read -r matrix_file M N nz <<< "$matrix_info"
    matrix_name=$(basename "$matrix_file")
    for to in "${thread_options[@]}"; do
        for cso in "${chunk_sizes_options[@]}"; do
            for so in "${scheduling_options[@]}"; do
                for i in {1..10}; do
                    exec_time=$(./main "$matrix_file" "$to" "$so" "$cso")
                    echo "$matrix_name,$M,$N,$nz,Nan,$to,$cso,$so,$exec_time" >> "$time_simulation_results"
                done
            done
        done
    done
done
echo "done."