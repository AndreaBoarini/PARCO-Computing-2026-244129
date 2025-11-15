cd ..
data_dir_path="./data"
cache_simulation_results="results/cache_results.csv"

compiler_options=("-O0" "-O1" "-O2" "-O3")
thread_options=(1 2 4 8 16 32 64)
chunk_sizes_options=(1 10 100 1000 10000)
scheduling_options=("static" "dynamic" "guided")
perf_start_options=("C" "W")
src_files=("./src/main.c" "./src/csr.c" "./src/print.c" "./src/mmio.c")

# Extract matrix info
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

# Csv header for cache results
echo "matrix_name,rows,cols,nz,compiler_option,thread_option,chunk_size_option,scheduling_option,perf_start,L1_loads,L1_misses,L1_misses_perc,LLC_loads,LLC_misses,LLC_misses_perc" > "$cache_simulation_results"

# Sequential caching simulation
echo "starting sequential caching..."
gcc -g -Iinclude -O3 "${src_files[@]}" -o main
    for matrix_info in "${input_matrices[@]}"; do
        IFS=',' read -r matrix_file M N nz <<< "$matrix_info"
        matrix_name=$(basename "$matrix_file")
        output=$(perf stat -x "," -e L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-misses ./main "C-N" "$matrix_file" 2>&1 | cut -d',' -f1 | head -n 4 | paste -sd ',')
        echo "$matrix_name,$M,$N,$nz,-O3,Nan,Nan,Nan,C-N,$output" >> "$cache_simulation_results"
    done
echo "done."

# Parallel caching simulation
echo "starting parallel caching..."
gcc -fopenmp -g -O3-Iinclude "${src_files[@]}" -o main
for matrix_info in "${input_matrices[@]}"; do
    IFS=',' read -r matrix_file M N nz <<< "$matrix_info"
    matrix_name=$(basename "$matrix_file")
    for to in "${thread_options[@]}"; do
        for cso in "${chunk_sizes_options[@]}"; do
            for so in "${scheduling_options[@]}"; do
                output=$(perf stat -x "," -e L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-misses ./main "C-N" "$matrix_file" "$to" "$so" "$cso" 2>&1 | cut -d',' -f1 | head -n 4 | paste -sd ',')
                echo "$matrix_name,$M,$N,$nz,-O3,$to,$cso,$so,C-N,$output" >> "$cache_simulation_results"
            done
        done
    done
done
echo "done."