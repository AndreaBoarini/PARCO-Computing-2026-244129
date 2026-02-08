#!/usr/bin/env python3
import os
import argparse
import numpy as np

def write_mtx_fixed_k(path, N, k, rng, vmin = -20.0, vmax = 20.0):
    if k > N:
        raise ValueError(f"k={k} > N={N} non possibile senza duplicati.")
    nz = N * k

    with open(path, "w", buffering=1024*1024) as f:
        f.write("%%MatrixMarket matrix coordinate real general\n")
        f.write(f"% synthetic random, fixed nnz per row = {k}\n")
        f.write(f"{N} {N} {nz}\n")

        for i in range(1, N + 1):
            cols = rng.choice(N, size=k, replace=False) + 1
            vals = rng.uniform(vmin, vmax, size=k)
            f.writelines(f"{i} {int(c)} {v:.15g}\n" for c, v in zip(cols, vals))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=str, default="weak_scaling_mtx")
    ap.add_argument("--nnz-per-row", type=int, default=32)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--vmin", type=float, default=-10.0)
    ap.add_argument("--vmax", type=float, default=10.0)
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    for exp in range(8, 17):
        N = 2**exp
        fn = f"synthetic_{N}x{N}_K{args.nnz_per_row}.mtx"
        path = os.path.join(args.outdir, fn)
        print(f"Generating {fn}: N={N}, k={args.nnz_per_row}, nz={N*args.nnz_per_row}")
        write_mtx_fixed_k(path, N, args.nnz_per_row, rng, args.vmin, args.vmax)

if __name__ == "__main__":
    main()
