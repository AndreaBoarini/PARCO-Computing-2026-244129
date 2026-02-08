import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import ScalarFormatter

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 12,               
    'axes.titlesize': 14,          
    'axes.labelsize': 12,          
    'xtick.labelsize': 11,         
    'ytick.labelsize': 11,         
    'legend.fontsize': 11,         
    'figure.titlesize': 14
})

def plot_efficiency_grouped(file_path):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"File '{file_path}' non trovato.")
        return

    df['total_time'] = df['computation_time'] + df['communication_time']
    

    baseline = df[df['procs'] == 1][['matrix_name', 'total_time']].rename(columns={'total_time': 't1'})
    df = df.merge(baseline, on='matrix_name')
    
    df['efficiency'] = df['t1'] / (df['procs'] * df['total_time'])

    plt.figure(figsize=(8, 6))

    sns.lineplot(data=df, x='procs', y='efficiency', hue='matrix_name', style='matrix_name', 
                 markers=True, dashes=False, linewidth=2.5, palette='viridis', zorder=10)


    ax = plt.gca()
    

    ax.set_xscale('log', base=2)
    used_procs = sorted(df['procs'].unique())
    ax.set_xticks(used_procs)
    ax.get_xaxis().set_major_formatter(ScalarFormatter())
    ax.minorticks_off()
    

    ax.set_ylim(0, 1.1)
    

    plt.title('Strong scaling - Parallel efficiency', fontweight='bold')
    plt.xlabel('Processes')
    plt.ylabel('Efficiency')
    

    plt.grid(True, linestyle='--', alpha=0.3)
    plt.legend(title='Matrix', loc='best', frameon=True, framealpha=0.9)


    output_filename = 'plots/efficiency_grouped.png'
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300, bbox_inches='tight', pad_inches=0.1)
    print(f"Grafico salvato: {output_filename}")

plot_efficiency_grouped('result/strong_test.csv')