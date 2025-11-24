import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import preprocess
import os

csv_filepath = "results/final_results_time.csv" 
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

print("Loading and preprocessing data...")
df_raw = pd.read_csv(csv_filepath)
df_90_perc = preprocess.preprocess_csv(df_raw)
print("Data preprocessing complete.")

os.makedirs(plots_dir, exist_ok=True)


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

    threads = sorted([int(t) for t in matrix_chunk_data["thread_option"].dropna().unique()])

    plt.figure(figsize=(10, 6))

    all_speedups_for_matrix = []

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
        
        all_speedups_for_matrix.extend([s for s in speedups if pd.notna(s)])

        plt.plot(
            threads,
            speedups,
            label=f"{schedule_type}",
            color=colors_schedule.get(schedule_type, 'gray'),
            marker='o',
            linestyle='-'
        )

    threads_for_ideal = sorted(list(set([1] + threads))) 
    plt.plot(
        threads_for_ideal,
        threads_for_ideal,
        color='gray', 
        linestyle='-.', 
        label='Ideal Speedup'
    )
    
    plt.axhline(y=1, color='red', linestyle='--', label='Sequential Time (Speedup = 1)')
    
    if all_speedups_for_matrix:
        max_speedup_value = np.max(all_speedups_for_matrix)
        
        max_y_limit = max_speedup_value * 1.6
        plt.ylim(0, max_y_limit)

        yticks, ylabels = plt.yticks()
        
        if not any(np.isclose(max_speedup_value, ytick, atol=0.01) for ytick in yticks):
            new_yticks = sorted(list(yticks) + [max_speedup_value])
            new_ylabels = [f'{y:.2f}' for y in new_yticks] 
            
            max_label = f'{max_speedup_value:.2f}'
            new_ylabels_bolded = [
                r'$\mathbf{' + label + '}$' if label == max_label else label
                for label in new_ylabels
            ]
            
            plt.yticks(new_yticks, new_ylabels_bolded)
        
        plt.axhline(y=max_speedup_value, color='black', linestyle=':', linewidth=0.8)
    
    plt.xlabel("Number of Threads")
    plt.ylabel("Speedup")
    plt.title(f"{matrix_name.replace('.mtx', '')} - Chunksize: {optimal_chunk_size}")
    plt.xticks(threads)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(title="Legend", loc='lower right')
    plt.tight_layout()

    filename = f"{matrix_name}_speedup.png"
    filepath = os.path.join(plots_dir, filename)
    plt.savefig(filepath)
    print(f"Saved speedup plot to: {filepath}")
    plt.close()

print("\nAll speedup plots generated and saved.")