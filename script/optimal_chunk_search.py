import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import preprocess

df = pd.read_csv("results/final_results_time.csv")

df_90_perc = preprocess.preprocess_csv(df)

schedule_order = ["static", "dynamic", "guided"]
colors_map = { 
    "static": {"color": "white", "edgecolor": "black"},
    "dynamic": {"color": "gray", "edgecolor": "black"},
    "guided": {"color": "black", "edgecolor": "black"}
}
width = 0.25

all_matrices = df_90_perc["matrix_name"].unique()

PLOTS_DIR = "plots/opc"
os.makedirs(PLOTS_DIR, exist_ok=True)

print("\nGenerating Plots for all Matrices and Chunk Sizes...\n")

for matrix_name in all_matrices:
    parallel_data = df_90_perc[
        (df_90_perc["matrix_name"] == matrix_name) & 
        (df_90_perc["thread_option"].notna()) &
        (df_90_perc["scheduling_option"].notna())
    ].copy()
    
    chunk_sizes = sorted(parallel_data["chunk_size_option"].unique())
    threads_list = sorted(parallel_data["thread_option"].unique())

    print(f"Processing Matrix: {matrix_name}")
    
    if not chunk_sizes or not threads_list:
        print(f"Warning: No parallel data found for matrix {matrix_name}. Skipping plot.")
        continue

    matrix_plot_dir = os.path.join(PLOTS_DIR, matrix_name)
    os.makedirs(matrix_plot_dir, exist_ok=True)

    seq_data = df_90_perc[(df_90_perc["matrix_name"] == matrix_name) & 
                          (df_90_perc["scheduling_option"].isna())]
    seq_time = seq_data["p90_exec_time"].iloc[0] if not seq_data.empty else np.nan

    for chunk in chunk_sizes:
        fig, ax = plt.subplots(figsize=(8, 5)) # Create a new figure and axis for each chunk
        chunk_data = parallel_data[parallel_data["chunk_size_option"] == chunk]
        
        axis_x = np.arange(len(threads_list))
        
        for i, sched in enumerate(schedule_order):
            sched_df = chunk_data[chunk_data["scheduling_option"] == sched]
            
            times = []
            for t in threads_list:
                row = sched_df[sched_df["thread_option"] == t]
                if not row.empty:
                    times.append(row["p90_exec_time"].iloc[0])
                else:
                    times.append(np.nan)
            
            offset_x = axis_x + (i - 1) * width
            
            style = colors_map[sched]
            ax.bar(
                offset_x,
                times,
                width=width,
                label=sched,
                color=style["color"],
                edgecolor=style["edgecolor"]
            )

        if not np.isnan(seq_time):
            ax.axhline(
                y=seq_time, 
                color="blue",
                linestyle="--",
                label="Sequential Time"
            )
        
        ax.set_xticks(axis_x)
        ax.set_xticklabels(threads_list)
        ax.set_xlabel("Threads")
        ax.set_ylabel("Execution time [ms]")
        ax.set_title(f"Performance Analysis for Matrix: {matrix_name}, Chunk Size: {chunk}")
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        
        ax.legend(title="Scheduling")

        plt.tight_layout()
        
        filename = f"{matrix_name}_OPC_chunk{chunk}.png"
        filepath = os.path.join(matrix_plot_dir, filename)
        plt.savefig(filepath)
        print(f"Saved plot to: {filepath}")
        plt.close(fig)

print("\nAll matrix and chunk size plots generated and saved to their respective subdirectories.")