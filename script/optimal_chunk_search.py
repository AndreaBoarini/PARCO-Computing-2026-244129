import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import preprocess

# Load data from the specified path
df = pd.read_csv("results/time_results_PRIVATE.csv")

# Get csv already preprocessed
df_90_perc = preprocess.preprocess_csv(df)

# Style parameters for the graph
schedule_order = ["static", "dynamic", "guided"]
colors_map = { 
    "static": {"color": "white", "edgecolor": "black"},
    "dynamic": {"color": "gray", "edgecolor": "black"},
    "guided": {"color": "black", "edgecolor": "black"}
}
width = 0.25

# Get all unique matrices for iteration
all_matrices = df_90_perc["matrix_name"].unique()

# Create the plots directory if it doesn't exist
PLOTS_DIR = "plots/PRIV"
os.makedirs(PLOTS_DIR, exist_ok=True)

print("\nGenerating Plots for all Matrices...\n")

for matrix_name in all_matrices:
    # Filter parallel data for the current matrix
    parallel_data = df_90_perc[
        (df_90_perc["matrix_name"] == matrix_name) & 
        (df_90_perc["thread_option"].notna()) &
        (df_90_perc["scheduling_option"].notna())
    ].copy()
    
    # Extract unique and sorted values for Chunk Size and Thread Option
    chunk_sizes = sorted(parallel_data["chunk_size_option"].unique())
    threads_list = sorted(parallel_data["thread_option"].unique())

    print(f"Processing Matrix: {matrix_name}")
    
    if not chunk_sizes or not threads_list:
        print(f"Warning: No parallel data found for matrix {matrix_name}. Skipping plot.")
        continue

    # Determine grid layout (rows x cols)
    n_chunks = len(chunk_sizes)
    n_cols = 3 
    n_rows = int(np.ceil(n_chunks / n_cols))

    fig, axes = plt.subplots(n_rows, n_cols, 
                             figsize=(4 * n_cols, 4 * n_rows), 
                             sharey=False) 
    
    # Handle single subplot case
    if n_chunks == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    # Calculate sequential time for the matrix (reference line)
    seq_data = df_90_perc[(df_90_perc["matrix_name"] == matrix_name) & 
                          (df_90_perc["scheduling_option"].isna())]
    seq_time = seq_data["p90_exec_time"].iloc[0] if not seq_data.empty else np.nan

    # Iterate through each chunk size to create a subplot
    for idx, chunk in enumerate(chunk_sizes):
        ax = axes[idx]
        chunk_data = parallel_data[parallel_data["chunk_size_option"] == chunk]
        
        axis_x = np.arange(len(threads_list))
        
        # Iterate through scheduling types (static, dynamic, guided)
        for i, sched in enumerate(schedule_order):
            sched_df = chunk_data[chunk_data["scheduling_option"] == sched]
            
            times = []
            for t in threads_list:
                # Retrieve time for the specific combination (Chunk, Thread, Schedule)
                row = sched_df[sched_df["thread_option"] == t]
                if not row.empty:
                    times.append(row["p90_exec_time"].iloc[0])
                else:
                    times.append(np.nan)
            
            # Calculate offset to group bars
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

        # Add horizontal sequential time line (if available)
        if not np.isnan(seq_time):
            ax.axhline(
                y=seq_time, 
                color="blue",
                linestyle="--",
                label="Sequential Time"
            )
        
        # Set X-axis labels and subplot title
        ax.set_xticks(axis_x)
        ax.set_xticklabels(threads_list)
        ax.set_xlabel("Threads")
        ax.set_title(f"Chunk Size: {chunk}")
        ax.grid(axis="y", linestyle="--", alpha=0.5)

        # Add Y-label only to subplots in the first column
        if idx % n_cols == 0:
            ax.set_ylabel("Execution time (90th percentile, ms)")

    # Set overall title
    fig.suptitle(f"Performance Analysis for Matrix: {matrix_name}", fontsize=14)
    
    # Add legend
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, title="Scheduling", loc='upper right', bbox_to_anchor=(0.98, 0.95))

    # Hide empty subplots
    for i in range(n_chunks, n_rows * n_cols):
        fig.delaxes(axes[i])
        
    plt.tight_layout(rect=[0.05, 0.0, 1, 0.95])
    
    # Save plot
    filename = f"{matrix_name}_OPC.png"
    filepath = os.path.join(PLOTS_DIR, filename)
    plt.savefig(filepath)
    print(f"Saved plot to: {filepath}")
    plt.close(fig) # Close the figure to free up memory

print("\nAll matrix plots generated and saved to the 'plots' directory.")