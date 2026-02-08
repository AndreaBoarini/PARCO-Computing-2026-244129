import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import ScalarFormatter, FuncFormatter
import numpy as np

# --- CONFIGURAZIONE STILE REPORT ---
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'figure.titlesize': 14,
    # QUESTA È LA MODIFICA CHIAVE:
    # Imposta il render del testo matematico ($...$) usando il font 'regular' (lo stesso del resto)
    # invece del font matematico speciale (che è serif/corsivo).
    'mathtext.default': 'regular' 
})

def plot_grouped_speedup(file_path):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"File '{file_path}' non trovato.")
        return

    # Calcoli Speedup
    df['total_time'] = df['computation_time'] + df['communication_time']
    # Baseline: tempo a 1 processo per ogni matrice
    baseline = df[df['procs'] == 1][['matrix_name', 'total_time']].rename(columns={'total_time': 't1'})
    df = df.merge(baseline, on='matrix_name')
    df['measured_speedup'] = df['t1'] / df['total_time']

    # --- DIMENSIONE UNIFICATA (8x6) ---
    plt.figure(figsize=(8, 6))

    # 1. Plot Raggruppato
    sns.lineplot(data=df, x='procs', y='measured_speedup', hue='matrix_name', style='matrix_name',
                 markers=True, dashes=False, linewidth=2.5, palette='viridis', zorder=10)

    # 2. Plot Ideale (y=x)
    max_p = df['procs'].max()
    plt.plot([1, max_p], [1, max_p], 'k--', label='Ideal', alpha=0.6, linewidth=2, zorder=5)

    # 3. Impostazione Scale
    plt.xscale('log', base=2)
    plt.yscale('log', base=10)

    ax = plt.gca()

    # --- FORMATTAZIONE ASSE X (Processi) ---
    used_procs = sorted(df['procs'].unique())
    ax.set_xticks(used_procs)
    ax.get_xaxis().set_major_formatter(ScalarFormatter())
    ax.minorticks_off()
    
    # --- FORMATTAZIONE ASSE Y (Potenze di 10) ---
    def format_pow10(x, pos):
        # Calcola l'esponente base 10
        if x <= 0: return "" # Evita errori con log di numeri <= 0
        exponent = np.log10(x)
        
        # Formatta l'esponente come intero se possibile, altrimenti float
        if exponent.is_integer():
            exp_str = f"{int(exponent)}"
        else:
            exp_str = f"{exponent:.1f}"
            
        # Usa sintassi LaTeX per l'apice, ma grazie a 'mathtext.default': 'regular'
        # userà il font sans-serif standard.
        return f"$10^{{{exp_str}}}$"

    ax.yaxis.set_major_formatter(FuncFormatter(format_pow10))

    # Titoli e Label
    plt.title('Strong Scaling Speedup', fontweight='bold')
    plt.xlabel('Processes')
    plt.ylabel('Speedup (log10 scale)')
    
    # Griglia
    plt.grid(True, which="major", linestyle='--', alpha=0.4, color='grey')
    
    # Legenda
    plt.legend(title='Matrix', loc='best', frameon=True, framealpha=0.9)

    output_filename = 'speedup_grouped_pow10_sans.png'

    # --- SALVATAGGIO ---
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300, bbox_inches='tight', pad_inches=0.1)
    print(f"Grafico salvato: {output_filename}")
    # plt.show()

# Esegui la funzione
plot_grouped_speedup('results/strong_test.csv')