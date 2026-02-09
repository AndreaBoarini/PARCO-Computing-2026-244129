import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import ScalarFormatter, FuncFormatter
import numpy as np

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'figure.titlesize': 14,
    'mathtext.default': 'regular' 
})

def plot_grouped_speedup(file_path):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"File '{file_path}' non trovato.")
        return

    df['total_time'] = df['computation_time'] + df['communication_time']
    baseline = df[df['procs'] == 1][['matrix_name', 'total_time']].rename(columns={'total_time': 't1'})
    df = df.merge(baseline, on='matrix_name')
    df['measured_speedup'] = df['t1'] / df['total_time']

    plt.figure(figsize=(8, 6))

    sns.lineplot(data=df, x='procs', y='measured_speedup', hue='matrix_name', style='matrix_name',
                 markers=True, dashes=False, linewidth=2.5, palette='viridis', zorder=10)

    max_p = df['procs'].max()
    plt.plot([1, max_p], [1, max_p], 'k--', label='Ideal', alpha=0.6, linewidth=2, zorder=5)

    plt.xscale('log', base=2)
    plt.yscale('log', base=10)

    ax = plt.gca()

    used_procs = sorted(df['procs'].unique())
    ax.set_xticks(used_procs)
    ax.get_xaxis().set_major_formatter(ScalarFormatter())
    ax.minorticks_off()
    
    def format_pow10(x, pos):
        if x <= 0: return ""
        exponent = np.log10(x)
        
        if exponent.is_integer():
            exp_str = f"{int(exponent)}"
        else:
            exp_str = f"{exponent:.1f}"
            
        return f"$10^{{{exp_str}}}$"

    ax.yaxis.set_major_formatter(FuncFormatter(format_pow10))

    plt.title('Strong Scaling Speedup', fontweight='bold')
    plt.xlabel('Processes')
    plt.ylabel('Speedup (log10 scale)')
    
    plt.grid(True, which="major", linestyle='--', alpha=0.4, color='grey')
    
    plt.legend(title='Matrix', loc='best', frameon=True, framealpha=0.9)

    output_filename = 'plots/speedup_grouped_pow10_sans.png'

    plt.tight_layout()
    plt.savefig(output_filename, dpi=300, bbox_inches='tight', pad_inches=0.1)
    print(f"Grafico salvato: {output_filename}")

plot_grouped_speedup('result/strong_scaling.csv')