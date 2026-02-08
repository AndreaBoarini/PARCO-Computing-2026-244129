import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os

# --- CONFIGURAZIONE STILE REPORT ---
# Applica lo stesso stile dell'altro script per coerenza
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 12,               # Testo generale
    'axes.titlesize': 14,          # Titoli assi
    'axes.labelsize': 12,          # Label assi
    'xtick.labelsize': 11,         # Numeri asse X
    'ytick.labelsize': 11,         # Numeri asse Y
    'legend.fontsize': 11,         # Legenda
    'figure.titlesize': 14
})

# Configura il parser degli argomenti
parser = argparse.ArgumentParser(description='Genera grafici di scaling (Strong o Weak).')
parser.add_argument('--type', type=str, choices=['strong', 'weak'], required=True,
                    help='Tipo di scaling da analizzare: "strong" o "weak"')
parser.add_argument('--log', action='store_true',
                    help='Forza scala logaritmica (di default è già attiva per weak)')
parser.add_argument('--linear', action='store_true',
                    help='Forza scala lineare (utile per disattivare il log di default nel weak scaling)')

args = parser.parse_args()

# Determina se usare la scala logaritmica
use_log = False
if args.type == 'weak':
    use_log = True
if args.log:
    use_log = True
if args.linear:
    use_log = False

def generate_plot(df, title_suffix, filename, log_scale=False):
    # Ordina per numero di processi
    df_sorted = df.sort_values('procs')
    
    # Prepara i dati
    procs = df_sorted['procs'].astype(str)
    comp_time = df_sorted['computation_time']
    comm_time = df_sorted['communication_time']
    
    # --- DIMENSIONE UNIFICATA (8x6) ---
    plt.figure(figsize=(8, 6))
    
    # Disegna le barre
    plt.bar(procs, comp_time, label='Computation Time', color="#0d1161", zorder=3, edgecolor='black', linewidth=0.5)
    plt.bar(procs, comm_time, bottom=comp_time, label='Communication Time', color="#bbbbbb", zorder=3, edgecolor='black', linewidth=0.5)
    
    # Imposta la scala logaritmica
    if log_scale:
        plt.yscale('log')
        min_comp = comp_time[comp_time > 0].min()
        if pd.notna(min_comp):
             plt.ylim(bottom=min_comp / 2) 
        plt.ylabel('Time (ms) - Log Scale')
        title_extra = '(Log Scale)'
    else:
        plt.ylabel('Total Execution Time (ms)')
        title_extra = ''

    # Etichette e Titoli
    plt.xlabel('Processes')
    plt.title(f'{title_suffix} {title_extra}', fontweight='bold')
    plt.legend(frameon=True, framealpha=0.9) # Legenda leggibile
    
    # Griglia
    if log_scale:
        plt.grid(True, which="both", axis='y', linestyle='--', alpha=0.5, zorder=0)
    else:
        plt.grid(axis='y', linestyle='--', alpha=0.7, zorder=0)
    
    # --- SALVATAGGIO OTTIMIZZATO (No spazi bianchi) ---
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight', pad_inches=0.1)
    print(f"Grafico salvato: {filename}")
    plt.close()

# Logica principale
if args.type == 'strong':
    file_path = 'results/strong_test.csv'
    if not os.path.exists(file_path):
        if os.path.exists('strong_scaling.csv'): file_path = 'strong_scaling.csv'
        else:
             print(f"Errore: Il file '{file_path}' non esiste.")
             exit()
             
    df = pd.read_csv(file_path)
    matrices = df['matrix_name'].unique()

    for matrix in matrices:
        matrix_df = df[df['matrix_name'] == matrix]
        generate_plot(matrix_df, 
                      f'{matrix} - Strong Scaling', 
                      f"strong_scaling_{matrix}.png", 
                      log_scale=use_log)

elif args.type == 'weak':
    file_path = 'results/weak_test.csv'
    if not os.path.exists(file_path):
        if os.path.exists('weak_test.csv'): file_path = 'weak_test.csv'
        elif os.path.exists('weak_scaling.csv'): file_path = 'weak_scaling.csv'
        else:
             print(f"Errore: Il file '{file_path}' non esiste.")
             exit()

    df = pd.read_csv(file_path)
    generate_plot(df, 'Weak Scaling', "weak_scaling.png", log_scale=use_log)