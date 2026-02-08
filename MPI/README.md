# Setting up the environment
In order to start working with the project resources, connect to the Unitn's cluster (only for registered users) and clone the repository:
```
ssh username@hpc.unitn.it
git clone https://github.com/AndreaBoarini/PARCO-Computing-2026-244129.git
```
Download from the web the matrices that will be used for the measurements.
The `retrieve_inputs.sh` script automatically downloads the real matrix samples from https://sparse.tamu.edu used for the evaluations discussed in the `Boarini-244129-D2.pdf`.
Before executing it, it has to be made executable. The resulting inputs will be found in the `data/` directory, which is already populated of the syntethic matrixes used for weak scaling when the repository is cloned.
```
cd PARCO-Computing-2026-244129/MPI/scripts
chmod +x retrieve_inputs.sh
./retrieve_inputs.sh
```

> [!NOTE]
> Any kind of matrix can be used to test the strong scaling. However, please be aware of the following constraints:
> - It consists of a `.mtx` file
> - It is placed in the `/data` directory (the source program will fetch the data from there)
> - If it's symmetric, its file will represent only one half and MMIO library isn't able to automatically generate the other corresponding half by itself. The result will consist in only one half populated (the one read) and the other half filled with zeros.

# General repository infos
The repository is now structured as follows:
```
PARCO-Computing-2026-244129/MPI
├── README.md               
├── data/
│   ├── synthetic_mtx1.mtx
│   ├── synthetic_mtx2.mtx
│   └── ...
├── src/
│   ├── main.c
│   ├── csr.c
│   ├── mmio.c
│   └── ghost.c
├── include/
│   ├── csr.h
│   ├── mmio.h
│   ├── ghost.h
│   └── structures.h
├── script/
│   ├── run.pbs
│   ├── retrieve_input.sh
│   ├── cnorm_and_memory.py
│   ├── parallel_efficiency.py
│   ├── speedup_strong.py
│   ├── synthetic_generator.sh
│   └── time_breakdown.sh                 
├── results/
│   ├── strong_scaling.csv
│   └── weak_scaling.csv
├── plots/
│   ├── metrics/
│       ├── plot1.png
│       ├── ...
│       └── plot2.png
│   └── scaling/
│       ├── plot1.png
│       ├── ...
│       └── plot2.png
└── report.pdf 
```
The execution of all the measurements is made possible by `run.pbs` which executes both strong scaling tests with the real matrixes and weak scaling test with the synthetic matrixes.
The script already takes care of importing the needed modules and setting the correct scheduling policies and resources allocation parameters.

The result both of the weak and strong scaling are then stored separately in `weak_scaling.csv` and `strong_scaling.csv` files in `result/` folder.

# Plotting the results
Once the complete `weak_scaling.csv` and `strong_scaling.csv` files are fully written, the data analysis and the plotting of the results can be conducted.
In the `script/` folder different `.py` scripts for different plots can be found. The plots generated are then stored in the `plots/` folder.
Some of the possible plots are:
- subplots (2) of Communication normalized volume per rank (above) and memory footprint per rank (below) --> invoke from the root `python3 script/cnorm_and_memory.py`
- parallel efficiency for all real samples (strong scaling) --> invoke from the root `pyhton3 script/parallel_efficiency.py`
- speedup for all real samples (strong scaling) --> invoke from the root `pyhton3 script/speedup_strong.py`
- time computation vs. communication breakdwon --> invoke from the root `pyhton3 script/time_breakdown.py -type strong` (if the plot has to be related to strong scaling records) or `pyhton3 script/time_breakdown.py -type weak` (if the plot has to be related to weak scaling records).
It's important to remark again that this automation is effective only after the complete `.csv` files are generated, otherwise
there wouldn't be sufficient information to plot charts and to make performance comparisons for all the different aspects as originally intended.

> [!CAUTION]
> Do NOT run any pyhton script for plotting on the cluster environment, instead, run it locally.
> This program uses `pandas` as a dependency, module that currently is not available to be imported in the cluster yet. If ran anyway the cluster python's interpreter
> will generate errors for not recognizing the import of the latter. Pyhton version used: 3.14.0.

The resulting images of the plots generated can be found in `plots/`. Note that some of them will be the same of the ones used in `Boarini-244129-D2.pdf` for results explanation.
Any run of the project will cause an **overwriting** both on the `.csv` and `.png` files which eventually will lead to different observable results than those reported
(if same inputs are used, the difference between the values although is minimal and does not affect on the conclusions of the research).

# Job submission
The Job submission is entrusted to the `script/run.pbs` script. It will essentially, instantiate a job with the required specifications for the project to run and will execute
the simulations.

Once in the root directory of the project:
```
cd script/
qsub run.pbs
```