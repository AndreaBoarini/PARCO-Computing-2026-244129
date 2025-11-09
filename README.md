# General repository infos
The current repository is structured as follows:
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
│   ├── data_analysis_and_plotting.py
│   └── run_simulation.py                 
├── results/
│   ├── plot1.png
│   ├── plot2.png
│   ├── ...
│   └── results.csv
└── report.pdf 
```
The execution of all the measurements are made possible by `run_simulation.py` which executes,
for every single combination of matrix as input, compiler option, number of thread among the specified set,
scheduling option and chunk size in the specified set, the computation of the elapsed time for the SpMV multiplication.

Very briefly, the script invokes two compilation directives (one for sequential execution and one for parallel execution)
and run the executable `./main` as many time needed to satisfy all the possible combinations.
The results both of the elapsed times and cache misses info are then stored separately in `results.csv` file.

> [!Warning]
> The simulation script has been extensively tested in the Unitn cluster's environment. In order to reproduce correctly the
> wanted output and avoid compiling/execution errors it's warmly recommended to use `python-3.10.14` and `gcc-9.1.0` as modules
> (can be directly loaded from the cluster's module list).

# Reproducing the results
As well as reproducing all the measurements, it's also possible to observe the elapsed time output under a specific setup condition.
To run the algorithm **sequentially** use the following command in the direcotry folder:
```
gcc -g -Iinclude -<compiler-optimization> src/main.c src/csr.c src/mmio.c src/print.c -o main
./main data/<matrix-input>
```
Or to operate **parallely**:
```
gcc -g -Iinclude -fopenmp -<compiler-optimization> src/main.c src/csr.c src/mmio.c src/print.c -o main
./main data/<matrix-input> <thread-number> <scheduling-option> <chunk-size>
```
For unaccepted directive formats (e.g. too many/few arguments) the program will automatically detect the error and abort the process.
The result of the computation is expressed in ms (microseconds).
Please, note also that the output for the individual run is not stored anywhere but is meant for testing only.

> [!NOTE]
> In the project direcotry can be found useful print functions that can be called in the source file (`src/main.c`) with the aim to
> print additional informations regarding the execution of the algorithm (e.g. display th result vector, display the input matrix in CSR format, etc...)
> Please, check `include/print.h` for the list of all the callable routines.

# Plotting the results
Once the complete `results.csv` file is obtained, the data analysis and the plotting of the results can be conducted. The `data_analysis_and_plotting.py` file is
encharged of this process. It's important to remark again that this automation is effective only after a rich and complete `results.csv` is generated, otherwise
there wouldn't be sufficient information to plot charts and to make performance comparisons for all the different aspects as originally intended.

> [!CAUTION]
> Do NOT run `data_analysis_and_plotting.py` in the cluster environment, instead, run it locally.
> This program uses `pandas` as a dependency, module that currently is not available to be imported in the cluster yet. If ran anyway the cluster python's interpreter
> will generate errors for not recognizing the import of the latter.

The resulting images of the plots generated can be found in `results/`. Note that they'll be the same of the ones used in `report.pdf` for results explanation.
Any run of the project will cause an **overwriting** both on the `.csv` and `.png` files which eventually will lead to different observable results than those reported
on `report.pdf` (the difference between the values although is minimal does not affect the conlusions of the research).

# Job submission

# Step by step compilation and run
