import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import preprocess

# Load data from the specified path
df = pd.read_csv("results/final_results_time.csv")

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
PLOTS_DIR = "plots/opc"
os.makedirs(PLOTS_DIR, exist_ok=True)

print("\nGenerating Plots for all Matrices and Chunk Sizes...\n")

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

    # Create a subdirectory for the current matrix
    matrix_plot_dir = os.path.join(PLOTS_DIR, matrix_name)
    os.makedirs(matrix_plot_dir, exist_ok=True)

    # Calculate sequential time for the matrix (reference line)
    seq_data = df_90_perc[(df_90_perc["matrix_name"] == matrix_name) & 
                          (df_90_perc["scheduling_option"].isna())]
    seq_time = seq_data["p90_exec_time"].iloc[0] if not seq_data.empty else np.nan

    # Iterate through each chunk size to create a separate plot
    for chunk in chunk_sizes:
        fig, ax = plt.subplots(figsize=(8, 5)) # Create a new figure and axis for each chunk
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
        
        # Set X-axis labels and plot title
        ax.set_xticks(axis_x)
        ax.set_xticklabels(threads_list)
        ax.set_xlabel("Threads")
        ax.set_ylabel("Execution time [ms]")
        ax.set_title(f"Performance Analysis for Matrix: {matrix_name}, Chunk Size: {chunk}")
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        
        # Add legend
        ax.legend(title="Scheduling")

        plt.tight_layout()
        
        # Save plot in the matrix-specific subdirectory
        filename = f"{matrix_name}_OPC_chunk{chunk}.png"
        filepath = os.path.join(matrix_plot_dir, filename)
        plt.savefig(filepath)
        print(f"Saved plot to: {filepath}")
        plt.close(fig) # Close the figure to free up memory

print("\nAll matrix and chunk size plots generated and saved to their respective subdirectories.")