import csv, os
import pandas as pd
import subprocess

data_dir_path = "./data"

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

# run the sequential simulation with the matrices available
# in ./data and exploiting -O0, ... -Ofast optimization levels
print("starting sequential simulation...")
