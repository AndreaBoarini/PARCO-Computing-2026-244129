import csv, os
import subprocess

data_dir_path = "./data"
time_seq_simulation_results = "times_seq.csv"
time_par_simulation_results = "times_par.csv"

# extract from each file the matrices' intrinsics
input_matrices = []
for f in os.listdir(data_dir_path):
    if f.endswith(".mtx"):
        file_path = os.path.join(data_dir_path, f)
        with open(file_path, 'r') as file:
            for line in file:
                if line.startswith('%'):
                    continue
                else:
                    parts = line.split()
                    M = int(parts[0])
                    N = int(parts[1])
                    nz = int(parts[2])
                    input_matrices.append((f, M, N, nz))
                    break

compiler_options = {"-O0", "-O1", "-O2", "-O3", "-Ofast"}
thread_options = {1, 2, 4, 8}
chunk_sizes_options = {1, 10, 100, 1000}
scheduling_options = {"static", "dynamic", "guided"}
src_files = {"src/main.c", "src/csr.c", "src/print.c", "src/mmio.c"}

# create the csv for time results
with open(time_seq_simulation_results, mode='w', newline='') as f:
    writer = csv.writer(f)
    header = ["matrix_name", "rows", "cols", "nz", "compiler_option", "thread_option", "chunk_size_option", "scheduling_option", "exec_time"]
    writer.writerow(header)

with open(time_par_simulation_results, mode='w', newline='') as f:
    writer = csv.writer(f)
    header = ["matrix_name", "rows", "cols", "nz", "compiler_option", "thread_option", "chunk_size_option", "scheduling_option", "exec_time"]
    writer.writerow(header)

# run the sequential simulation with the matrices available
# in ./data and exploiting -O0, ... -Ofast optimization levels
print("starting sequential simulation...")
for co in compiler_options:
    subprocess.run(["gcc", "-g", "-Iinclude", *src_files, co, "-o", "main"])
    for matrix in input_matrices:
        matrix_file, M, N, nz = matrix
        for i in range(1, 11):
            with open(time_seq_simulation_results, mode='a', newline='') as f:
                writer = csv.writer(f)
                result = subprocess.run(["./main", (data_dir_path + "/" + matrix_file)], capture_output=True, text=True)
                exec_time = result.stdout.strip()
                writer.writerow([matrix_file, M, N, nz, co, 'Nan', 'Nan', 'Nan', exec_time])
print("done.")

# run the parallel simulation with the same matrices
# with different number of threads, chunk sizes and scheduling options
print("starting parallel simulation...")
subprocess.run(["gcc", "-fopenmp", "-g", "-Iinclude", *src_files, "-o", "main"])
for matrix in input_matrices:
    matrix_file, M, N, nz = matrix 
    for to in thread_options:
        for cso in chunk_sizes_options:
            for so in scheduling_options:
                for i in range(1, 11):
                    with open(time_par_simulation_results, mode='a', newline='') as f:
                        writer = csv.writer(f)
                        result = subprocess.run(["./main", (data_dir_path + "/" + matrix_file), str(to), so, str(cso)], capture_output=True, text=True)
                        exec_time = result.stdout.strip()
                        writer.writerow([matrix_file, M, N, nz, 'Nan', to, cso, so, exec_time])
print("done.")