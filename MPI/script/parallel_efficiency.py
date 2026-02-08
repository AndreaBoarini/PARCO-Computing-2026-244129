import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import ScalarFormatter

# --- CONFIGURAZIONE STILE REPORT (Normalizzazione) ---
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

def plot_efficiency_grouped(file_path):
    # 1. Caricamento Dati
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"File '{file_path}' non trovato.")
        return

    # 2. Calcoli Efficiency
    # Formula: Efficiency = Speedup / p = T1 / (p * Tp)
    df['total_time'] = df['computation_time'] + df['communication_time']
    
    # Estrazione Baseline (Tempo a 1 processo)
    baseline = df[df['procs'] == 1][['matrix_name', 'total_time']].rename(columns={'total_time': 't1'})
    df = df.merge(baseline, on='matrix_name')
    
    # Calcolo colonna Efficienza
    df['efficiency'] = df['t1'] / (df['procs'] * df['total_time'])

    # --- DIMENSIONE UNIFICATA (8x6) ---
    plt.figure(figsize=(8, 6))

    # 3. Plotting
    # Utilizziamo 'hue' per colorare diversamente le matrici
    # 'style' aggiunge marker diversi per accessibilità
    sns.lineplot(data=df, x='procs', y='efficiency', hue='matrix_name', style='matrix_name', 
                 markers=True, dashes=False, linewidth=2.5, palette='viridis', zorder=10)

    # 4. Formattazione Assi
    ax = plt.gca()
    
    # Asse X: Logaritmica base 2 (1, 2, 4, 8...)
    ax.set_xscale('log', base=2)
    used_procs = sorted(df['procs'].unique())
    ax.set_xticks(used_procs)
    ax.get_xaxis().set_major_formatter(ScalarFormatter())
    ax.minorticks_off()
    
    # Asse Y: Limitato tra 0 e 1.1 (l'efficienza ideale è 1.0)
    ax.set_ylim(0, 1.1)
    
    # Titoli e Label
    plt.title('Strong scaling - Parallel efficiency', fontweight='bold')
    plt.xlabel('Processes')
    plt.ylabel('Efficiency')
    
    # Griglia e Legenda
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.legend(title='Matrix', loc='best', frameon=True, framealpha=0.9)

    # --- SALVATAGGIO OTTIMIZZATO ---
    output_filename = 'efficiency_grouped.png'
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300, bbox_inches='tight', pad_inches=0.1)
    print(f"Grafico salvato: {output_filename}")
    # plt.show()

# Esegui la funzione
plot_efficiency_grouped('results/strong_test.csv')