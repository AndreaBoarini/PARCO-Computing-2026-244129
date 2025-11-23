import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# --- FUNZIONI DI PREPROCESSING INTEGRATE ---
def compute_block_percentile90(group):
    # Computes the 90th percentile of execution time in blocks of 10 measurements.
    results = []
    rows = group.shape[0]
    for i in range(0, rows, 10):
        block = group.iloc[i:i+10]
        if len(block) == 10:
            p90 = np.percentile(block["exec_time"], 90, method='lower')
            
            row_data = block.iloc[0][[
                "matrix_name", "compiler_option", "thread_option",
                "chunk_size_option", "scheduling_option"
            ]].to_dict()
            
            row_data["p90_exec_time"] = p90
            results.append(row_data)
            
    return pd.DataFrame(results)

def preprocess_csv(df):
    """Esegue la pre-elaborazione e calcola il 90° percentile per ogni blocco/configurazione."""
    
    df = df.replace({"Nan": np.nan, "NaN": np.nan})

    integer_cols = [
        "rows", "cols", "nz",
        "thread_option", "chunk_size_option"
    ]

    print("Starting type conversion...")
    for col in integer_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].astype('Int64')
    print("Type conversion complete.")

    df_sorted = df.sort_values([
        "matrix_name", "compiler_option", "thread_option",
        "chunk_size_option", "scheduling_option"
    ])

    df_90_perc = df_sorted.groupby([
        "matrix_name", "compiler_option",
        "thread_option", "chunk_size_option",
        "scheduling_option"
    ], dropna=False, group_keys=False).apply(compute_block_percentile90).reset_index(drop=True)

    return df_90_perc

# --- 1. CONFIGURATION (AGGIORNATA) ---

csv_filepath = "results/final_results_time.csv" 
plots_dir = "plots"

MATRIX_CONFIGS = {
    "bayer03.mtx": {"chunk_size": 1000, "label": "bayer03 (chunk: 1000)"},
    "G3_circuit.mtx": {"chunk_size": 10000, "label": "G3_circuit (chunk: 10000)"},
    "rajat31.mtx": {"chunk_size": 1000, "label": "rajat31 (chunk: 1000)"}, # <--- AGGIUNTA RAJAT31
}

BASE_COLOR_G3 = "#4490c6"
BASE_COLOR_B3 = "#e73d3d"
BASE_COLOR_R31 = "#ffb224" # <--- COLORE GIALLO PER RAJAT31

SCHEDULE_ORDER = ["static", "dynamic", "guided"] # Usato per l'iterazione, non più per gli shade

THEORETICAL_COLOR = "black"

# --- 2. DATA LOADING AND PREPROCESSING ---

df_raw = pd.read_csv(csv_filepath)
df_90_perc = preprocess_csv(df_raw)

os.makedirs(plots_dir, exist_ok=True)

# --- 3. SPEEDUP CALCULATION AND PLOTTING (MODIFICATO) ---

plot_data = {}
all_threads = []
all_max_speedups = {} # Per memorizzare lo speedup massimo raggiunto da ciascuna matrice

for matrix_name, config in MATRIX_CONFIGS.items():
    optimal_chunk_size = config["chunk_size"]
    
    matrix_chunk_data = df_90_perc[
        (df_90_perc["matrix_name"] == matrix_name) &
        (df_90_perc["chunk_size_option"].astype('Int64') == optimal_chunk_size)
    ].copy()

    # Tempo sequenziale (scheduling_option è NaN)
    sequential_time_df = df_90_perc[
        (df_90_perc["matrix_name"] == matrix_name) &
        (df_90_perc["scheduling_option"].isna())
    ]
    
    if sequential_time_df.empty:
        continue
    
    sequential_time = sequential_time_df["p90_exec_time"].iloc[0]

    if pd.isna(sequential_time) or sequential_time <= 0:
        continue

    threads = sorted([int(t) for t in matrix_chunk_data["thread_option"].dropna().unique()])
    all_threads.extend(threads)
    
    best_speedup = -1.0
    best_schedule_type = None
    best_schedule_speedups = {}
    
    # 3.1 Calcola lo Speedup per Tutte le Schedule
    all_schedule_speedups = {}
    
    for schedule_type in SCHEDULE_ORDER:
        schedule_data = matrix_chunk_data[
            matrix_chunk_data["scheduling_option"] == schedule_type
        ].copy()

        speedups = {}
        for t in threads:
            thread_schedule_time_df = schedule_data[schedule_data["thread_option"] == t]
            
            if not thread_schedule_time_df.empty:
                parallel_time = thread_schedule_time_df["p90_exec_time"].iloc[0]
                if pd.notna(parallel_time) and parallel_time > 0:
                    speedup = sequential_time / parallel_time
                    speedups[t] = speedup
                    
                    # 3.2 Trova lo speedup massimo e la schedule corrispondente
                    if speedup > best_speedup:
                        best_speedup = speedup
                        best_schedule_type = schedule_type
                        
                else:
                    speedups[t] = np.nan
            else:
                speedups[t] = np.nan
        
        all_schedule_speedups[schedule_type] = speedups
        
    # 3.3 Conserva solo la migliore schedule e il massimo speedup
    if best_schedule_type:
        best_schedule_speedups = all_schedule_speedups[best_schedule_type]
        
        plot_data[matrix_name] = {
            "label": f"{config['label']} ({best_schedule_type})", # Etichetta aggiornata
            "data": best_schedule_speedups,
            "threads": threads,
            "best_schedule": best_schedule_type
        }
        all_max_speedups[matrix_name] = best_speedup

# 4. PLOTTING (MODIFICATO)
final_threads = sorted([int(t) for t in list(set(all_threads))])

if not plot_data or not final_threads:
    pass
else:
    plt.figure(figsize=(12, 8))

    plt.rcParams.update({
    'font.size': 14,           
    'axes.titlesize': 18,      
    'axes.labelsize': 16,      
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'legend.fontsize': 14,
    'legend.title_fontsize': 16
    })

    color_map = {
        "bayer03.mtx": BASE_COLOR_B3,
        "G3_circuit.mtx": BASE_COLOR_G3,
        "rajat31.mtx": BASE_COLOR_R31 # <--- AGGIUNTA MAPPA COLORE
    }

    legend_handles = []
    all_speedups_overall = []
    
    # --- Tracciamento SOLO della Migliore Strong Scaling ---
    for matrix_name, data in plot_data.items():
        base_color = color_map[matrix_name]
        
        speedups_dict = data["data"]
        threads_to_plot = [t for t in data["threads"] if t in speedups_dict]
        speedups_to_plot = [speedups_dict.get(t, np.nan) for t in threads_to_plot]
        
        all_speedups_overall.extend([s for s in speedups_to_plot if pd.notna(s)])

        line, = plt.plot(
            threads_to_plot,
            speedups_to_plot,
            label=data['label'],
            color=base_color,
            alpha=1.0, # Alpha fisso dato che c'è solo una linea per matrice
            marker='o',
            linestyle='-',
            linewidth=2.5
        )
        legend_handles.append(line)

    # 2. Aggiungi Speedup Teorico e Sequenziale
    theoretical_x = sorted(list(set([1] + final_threads)))
    theoretical_y = theoretical_x

    theoretical_handle, = plt.plot(
        theoretical_x,
        theoretical_y,
        color=THEORETICAL_COLOR,
        linestyle='--',
        linewidth=2,
        zorder=0
    )
    legend_handles.append(theoretical_handle)
    
    sequential_handle = plt.axhline(y=1, color='lime', linestyle='--', label='Sequential speedup', linewidth=2.7)
    legend_handles.append(sequential_handle)
    
    # --- Gestione Asse Y (Dilatato e Bolding) ---
    max_speedup_achieved_overall = np.nanmax(all_speedups_overall) if all_speedups_overall else 1
    max_y_limit = max_speedup_achieved_overall * 1.25 
    plt.ylim(0, max_y_limit)
    
    # Tutti gli speedup massimi da evidenziare
    max_speedup_to_bold = list(all_max_speedups.values())
    
    if max_speedup_achieved_overall > 0:
        yticks, _ = plt.yticks()
        
        # Aggiungi gli speedup massimi di ogni matrice se non già presenti
        new_yticks_set = set(yticks)
        for s in max_speedup_to_bold:
             if not any(np.isclose(s, ytick, atol=0.01) for ytick in yticks):
                 new_yticks_set.add(s)
                 
        new_yticks = sorted(list(new_yticks_set))
        new_ylabels = [f'{y:.2f}' for y in new_yticks] 
        
        # Bolding per i valori massimi di speedup di ciascuna matrice
        new_ylabels_bolded = []
        for y, label in zip(new_yticks, new_ylabels):
            is_max_speedup = any(np.isclose(y, max_val, atol=0.01) for max_val in max_speedup_to_bold)
            
            if is_max_speedup:
                new_ylabels_bolded.append(r'$\mathbf{' + label + '}$' if is_max_speedup else label)
            else:
                 new_ylabels_bolded.append(label)
            
        plt.yticks(new_yticks, new_ylabels_bolded)
    
    # --- GESTIONE LEGGENDA: SEMPLIFICATA ---
    
    matrix_labels = [data['label'] for data in plot_data.values()]
    other_labels = ["Theoretical Speedup"]

    final_labels = matrix_labels + other_labels
    
    # Plot della singola legenda
    plt.legend(legend_handles, final_labels, 
               title="Legend Summary", 
               loc='upper right', 
               framealpha=0.9,
               ncol=1) 
    
    # --- Titoli e Griglia ---
    plt.xlabel("Number of Threads")
    plt.ylabel("Speedup")
    
    title_matrix_names = " vs ".join([cfg['label'].split('(')[0].strip() for cfg in MATRIX_CONFIGS.values()])
    plt.title(f"Strong Scaling Comparison (Best Schedule): {title_matrix_names}", fontsize=14)
    
    plt.xticks(final_threads)
    plt.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout()

    filename = "strong_scaling_best_schedule.png"
    filepath = os.path.join(plots_dir, filename)
    plt.savefig(filepath)
    plt.close()
    
print(f"Grafico salvato in: {filepath}")