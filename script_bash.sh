#!/bin/bash

data_dir_path="./results"
time_simulation_results="time_results.csv"
cache_simulation_results="cache_results.csv"

compiler_options=("-O0" "-O1" "-O2" "-O3")
thread_options=(1 2 4 8)
chunk_sizes_options=(1 10 100 1000)
scheduling_options=("static" "dynamic" "guided")
perf_start_options=("C" "W")
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


# Csv header for time results
echo "matrix_name,rows,cols,nz,compiler_option,thread_option,chunk_size_option,scheduling_option,exec_time" > "$time_simulation_results"
# Csv header for cache results
echo "matrix_name,rows,cols,nz,compiler_option,thread_option,chunk_size_option,scheduling_option,perf_start,L1_loads,L1_misses,L1_misses_perc,LLC_loads,LLC_misses,LLC_misses_perc" > "$cache_simulation_results"



# Sequential simulation
echo "starting sequential simulation..."
for co in "${compiler_options[@]}"; do
    gcc -g -Iinclude "${src_files[@]}" "$co" -o main
    for matrix_info in "${input_matrices[@]}"; do
        IFS=',' read -r matrix_file M N nz <<< "$matrix_info"
        matrix_name=$(basename "$matrix_file")
        outputs=$(./main "W" "$matrix_file")
        while read -r exec_time; do
            echo "$matrix_name,$M,$N,$nz,$co,Nan,Nan,Nan,$exec_time" >> "$time_simulation_results"
        done <<< "$outputs"
    done
done
echo "done."

# Sequential caching simulation
echo "starting sequential caching..."
for co in "${compiler_options[@]}"; do
    gcc -g -Iinclude "${src_files[@]}" "$co" -o main
    for matrix_info in "${input_matrices[@]}"; do
        IFS=',' read -r matrix_file M N nz <<< "$matrix_info"
        matrix_name=$(basename "$matrix_file")
        for pso in "${perf_start_options[@]}"; do
            output=$(perf stat -e L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-misses ./main "$pso" "$matrix_file" 2>&1)
            L1_loads=$(echo "$output" | grep 'L1-dcache-loads' | awk '{print $1}')
            L1_misses=$(echo "$output" | grep 'L1-dcache-load-misses' | awk '{print $1}')
            LLC_loads=$(echo "$output" | grep 'LLC-loads' | awk '{print $1}')           
            LLC_misses=$(echo "$output" | grep 'LLC-misses' | awk '{print $1}')
            L1_miss_perc=$(echo "$output" | grep 'L1-dcache-load-misses' | awk '{print $4}')
            LLC_miss_perc=$(echo "$output" | grep 'LLC-misses' | awk '{print $4}')
            echo "$matrix_name,$M,$N,$nz,$co,Nan,Nan,Nan,$pso,$L1_loads,$L1_misses,$L1_miss_perc,$LLC_loads,$LLC_misses,$LLC_miss_perc" >> "$cache_simulation_results"
        done
    done
done
echo "done."

: '
# Parallel simulation
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

# Parallel caching simulation
echo "starting parallel caching..."
gcc -fopenmp -g -Iinclude "${src_files[@]}" -o main
for matrix_info in "${input_matrices[@]}"; do
    IFS=',' read -r matrix_file M N nz <<< "$matrix_info"
    matrix_name=$(basename "$matrix_file")
    for to in "${thread_options[@]}"; do
        for cso in "${chunk_sizes_options[@]}"; do
            for so in "${scheduling_options[@]}"; do
                for i in {1..5}; do
                    output=$(perf stat -e L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-misses ./main "$matrix_file" "$to" "$so" "$cso" 2>&1)
                    L1_loads=$(echo "$output" | grep 'L1-dcache-loads' | awk '{print $1}')
                    L1_misses=$(echo "$output" | grep 'L1-dcache-load-misses' | awk '{print $1}')
                    LLC_loads=$(echo "$output" | grep 'LLC-loads' | awk '{print $1}')           
                    LLC_misses=$(echo "$output" | grep 'LLC-misses' | awk '{print $1}')
                    L1_miss_perc=$(echo "$output" | grep 'L1-dcache-load-misses' | awk '{print $4}')
                    LLC_miss_perc=$(echo "$output" | grep 'LLC-misses' | awk '{print $4}')
                    echo "$matrix_name,$M,$N,$nz,Nan,$to,$cso,$so,$L1_loads,$L1_misses,$L1_miss_perc,$LLC_loads,$LLC_misses,$LLC_miss_perc" >> "$cache_simulation_results"
                done
            done
        done
    done
done
echo "done."
: '