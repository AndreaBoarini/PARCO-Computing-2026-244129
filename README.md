# Setting up the environment
In order to start working with the project resources, connect to the Unitn's cluster (only for registered users) and clone the repository:
```
ssh username@hpc.unitn.it
git clone https://github.com/AndreaBoarini/PARCO-Computing-2026-244129.git
```
Download from the web the matrices that will be used for the measurements.
The `retrieve_inputs.sh` script automatically downloads the matrix samples from https://sparse.tamu.edu used for the evaluations discussed in the `Boarini-244129-D1.pdf`.
Before executing it, it has to be made executable. The resulting inputs will be found in the `data/` direcorty, which is not present when firstly cloned.
```
cd PARCO-Computing-2026-244129/scripts
chmod +x retrieve_inputs.sh
./retrieve_inputs.sh
```
> [!NOTE]
> Any kind of matrix can be used to compute the results that will be stored in the two different `.csv` files, as long as:
> - It consists of a `.mtx` file
> - It is placed in the `/data` direcotry (the source program will fetch the data from there)
> - It is *NOT* a symmetric matrix (these types formatted differently and the MMIO library by not implementing any kind of function that satisfy this format won't read the matrix correctly)

# General repository infos
The repository is now structured as follows:
```
PARCO-Computing-2026-244129/
├── README.md               
├── data/
│   ├── matrix1.mtx
│   ├── matrix2.mtx
│   └── ...
├── src/
│   ├── main.c
│   ├── csr.c
│   ├── mmio.c
│   └── print.c
├── include/
│   ├── csr.h
│   ├── mmio.h
│   ├── print.h
│   └── timer.h
├── scripts/
│   ├── preprocess.py
│   ├── class_speedup.py
│   ├── LLC_miss_rate.py
│   ├── optimal_chunk_search.py
│   ├── plot_speedup.py
│   ├── run_job.pbs
│   ├── retrieve_inputs.sh
│   ├── cache_script.sh
│   └── time_script.sh                 
├── results/
│   ├── final_cache_results.csv
│   ├── final_time_results.csv
│   └── time_results_PRIVATE_NOEXP.csv
├── plots/
│   ├── plot1.png
│   ├── ...
│   └── plot_n.png
└── report.pdf 
```
The execution of all the measurements is made possible by `run_simulation.sh` which executes,
for every single combination of matrix as input, compiler option, number of thread among the specified set,
scheduling option and chunk size in the specified set, the computation of the elapsed time for the SpMV multiplication.
The script will also take care of the cache adresses' evaluations for each execution.

The results both of the elapsed times and cache misses info are then stored separately in `time_results.csv` and `cache_results.csv`

> [!Warning]
> The simulation script has been extensively tested in the Unitn cluster's environment. In order to reproduce correctly the
> wanted output and avoid compiling/execution errors it's warmly recommended to use `perf`and `gcc-9.1.0` as modules
> (can be directly loaded from the cluster's module list).
> The `run_job.pbs` script will sort out this automatically.

# Reproducing the results singularely
As well as reproducing all the measurements, it's also possible to observe the elapsed time output under a specific setup condition.
To run the algorithm **sequentially** use the following command in the root directory of the project:
```
gcc -g -Iinclude -<compiler-optimization> src/main.c src/csr.c src/mmio.c src/print.c -o main
```
```
./main <perf_cold_start> data/<matrix-input>
```
Or to operate **parallely**:
```
gcc -g -Iinclude -fopenmp -<compiler-optimization> src/main.c src/csr.c src/mmio.c src/print.c -o main
```
```
./main <perf-cold-start> data/<matrix-input> <thread-number> <scheduling-option> <chunk-size>
```
The `perf-cold-start` can either be `W` or `C` whether if it's necessary to execuite the parallel loop 10 times (with 10 outputs) or just once
(with a single output)
For unaccepted directive formats (e.g. too many/few arguments) the program will automatically detect the error and abort the process.
The result of the computation is expressed in ms (microseconds).
Please, note also that the output for the individual run is not stored anywhere but is meant for testing only.

Alternatively, to evaluate cache misses in a specific condition, firstly compile the project in as preferred (check above) and then run `perf stat`
command on the executable. In the scope of this project the elements taken into accounts where: L1 loads, L1 loads misses, LLC loads, LLC misses:
```
perf stat -e L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-misses ./main <matrix-input>
```

> [!NOTE]
> In the project `include/` directory can be found useful print functions that can be called in the source file (`src/main.c`) with the aim to
> print additional informations regarding the execution of the algorithm (e.g. display th result vector, display the input matrix in CSR format, etc...)
> Please, check `include/print.h` for the list of all the callable routines.
> This feature is initially disabled.

# Plotting the results
Once the complete `final_time_results.csv` and `final_cache_results.csv` files are obtained, and stored in `results/`, the data analysis and the plotting of the results can be conducted.
In the `script/` folder different `.py` scripts for different plots can be found. The plots generated are then stored in the `plots/` folder.
Some of the possible plots are:
- optimal chunk search to identify the best chunk for each matrix --> invoke from the root `python3 script/optimal_chunk_search.py`
- speedup for all matrices with the best chunksize already configurated --> invoke from the root `pyhton3 script/plot_speedup.py`
- LLC miss rate as number of threads increases --> invoke from the root `pyhton3 script/LLC_miss_rate.py`
- strong scaling with the best schedule for different dimension classes --> invoke from the root `pyhton3 script/class_speedup.py`
It's important to remark again that this automation is effective only after the complete `.csv` files are generated, otherwise
there wouldn't be sufficient information to plot charts and to make performance comparisons for all the different aspects as originally intended.

> [!CAUTION]
> Do NOT run any pyhton script for plotting on the cluster environment, instead, run it locally.
> This program uses `pandas` as a dependency, module that currently is not available to be imported in the cluster yet. If ran anyway the cluster python's interpreter
> will generate errors for not recognizing the import of the latter. Pyhton version used: 3.14.0.

The resulting images of the plots generated can be found in `plots/`. Note that some of them will be the same of the ones used in `Boarini-244129-D1.pdf` for results explanation.
Any run of the project will cause an **overwriting** both on the `.csv` and `.png` files which eventually will lead to different observable results than those reported
(if same inputs are used, the difference between the values although is minimal and does not affect on the conclusions of the research).

# Job submission
The Job submission is entrusted to the `scripts/run_job.pbs` script. It will essentially, instantiate a job with the required specifications for the project to run and will execute
the simulations script. The `.pbs` script will take care to load the modules cited above automatically.

> [!NOTE]
> The Job script is encharged of loading the module `gcc91` and `perf` by itself.
> There might be a chance that after `gcc91` is loaded command `gcc` might not point directly to `GCC9.1.0`.
> To overcome this issue please follow this routine:
> ```
> nano ~/bash.rc
> module load gcc91
> alias gcc=gcc-9.1.0
> source ~/bash.rc
> ```
> Now `gcc --version` should show `gcc-9.1.0`, which means everything is set up and your good to go.
> Note that this step has to be done only once for every different profile that starts the job.

Once in the root directory of the project:
```
cd script/
qsub run_job.pbs
```
This command will call both `final_time_results.sh` and `cache_final_results.sh` to start the simulations.
