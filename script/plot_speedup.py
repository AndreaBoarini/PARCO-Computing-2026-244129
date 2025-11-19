import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import preprocess

# --- 1. CONFIGURATION ---

csv_filepath = "results/time_results_PRIVATE.csv"
plots_dir = "plots/speedup"

chunk_size_map = {
    "rajat31.mtx": 1000,
    "memplus.mtx": 100,
    "G3_circuit.mtx": 10000,
    "cage13.mtx": 10000,
    "bayer03.mtx": 1000,
}

schedule_order = ["static", "dynamic", "guided"]

colors_schedule = {
    "static": "#1f77b4",
    "dynamic": "#2ca02c",
    "guided": "#ff7f0e"
}

# --- 2. DATA LOADING AND PREPROCESSING ---

print("Loading and preprocessing data...")
df_raw = pd.read_csv(csv_filepath)
df_90_perc = preprocess.preprocess_csv(df_raw)
print("Data preprocessing complete.")

os.makedirs(plots_dir, exist_ok=True)

# --- 3. SPEEDUP CALCULATION AND PLOTTING ---

print("\n--- Generating Speedup Plots ---")

for matrix_name, optimal_chunk_size in chunk_size_map.items():
    print(f"Processing matrix: {matrix_name} with optimal chunk size: {optimal_chunk_size}")

    matrix_chunk_data = df_90_perc[
        (df_90_perc["matrix_name"] == matrix_name) &
        (df_90_perc["chunk_size_option"] == optimal_chunk_size)
    ].copy()

    if matrix_chunk_data.empty:
        print(f"Warning: No data found for matrix {matrix_name} with chunk size {optimal_chunk_size}. Skipping.")
        continue

    sequential_time_df = df_90_perc[
        (df_90_perc["matrix_name"] == matrix_name) &
        (df_90_perc["scheduling_option"].isna())
    ]
    
    if sequential_time_df.empty:
        print(f"Warning: No sequential time found for matrix {matrix_name}. Cannot calculate speedup. Skipping.")
        continue
    
    sequential_time = sequential_time_df["p90_exec_time"].iloc[0]

    if pd.isna(sequential_time) or sequential_time == 0:
        print(f"Warning: Sequential time for {matrix_name} is invalid ({sequential_time}). Cannot calculate speedup. Skipping.")
        continue

    threads = sorted(matrix_chunk_data["thread_option"].unique())

    plt.figure(figsize=(10, 6))

    all_speedups_for_matrix = [] # Collect all speedups to find the overall max

    for schedule_type in schedule_order:
        schedule_data = matrix_chunk_data[
            matrix_chunk_data["scheduling_option"] == schedule_type
        ].copy()

        speedups = []
        for t in threads:
            thread_schedule_time_df = schedule_data[schedule_data["thread_option"] == t]
            
            if not thread_schedule_time_df.empty:
                parallel_time = thread_schedule_time_df["p90_exec_time"].iloc[0]
                if pd.notna(parallel_time) and parallel_time > 0:
                    speedup = sequential_time / parallel_time
                    speedups.append(speedup)
                else:
                    speedups.append(np.nan)
            else:
                speedups.append(np.nan)
        
        # Add current schedule's speedups to the overall list for max calculation
        all_speedups_for_matrix.extend([s for s in speedups if pd.notna(s)])

        plt.plot(
            threads,
            speedups,
            label=f"Scheduling: {schedule_type}",
            color=colors_schedule.get(schedule_type, 'gray'),
            marker='o',
            linestyle='-'
        )

    plt.axhline(y=1, color='red', linestyle='--', label='sequential)')
    
    # --- Add max speedup tick and value ---
    if all_speedups_for_matrix:
        max_speedup_value = np.max(all_speedups_for_matrix)
        
        # Get current y-ticks and labels
        yticks, ylabels = plt.yticks()
        
        # Add the max speedup value to yticks if it's not already very close to an existing one
        if not any(np.isclose(max_speedup_value, ytick, atol=0.01) for ytick in yticks):
            new_yticks = sorted(list(yticks) + [max_speedup_value])
            plt.yticks(new_yticks, [f'{y:.2f}' for y in new_yticks])
        
        # Draw a horizontal line at the max speedup point (optional, but helps visualize)
        plt.axhline(y=max_speedup_value, color='black', linestyle=':', linewidth=0.8, 
                    label=f'Max Speedup: {max_speedup_value:.2f}')
    
    plt.xlabel("Number of Threads")
    plt.ylabel("Speedup")
    # --- Matrix name in bold ---
    plt.title(f"{matrix_name.replace('.mtx', '')} - Chunksize: {optimal_chunk_size}")
    plt.xticks(threads)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(title="Legend")
    plt.tight_layout()

    filename = f"{matrix_name}_speedup.png"
    filepath = os.path.join(plots_dir, filename)
    plt.savefig(filepath)
    print(f"Saved speedup plot to: {filepath}")
    plt.close()

print("\nAll speedup plots generated and saved.")