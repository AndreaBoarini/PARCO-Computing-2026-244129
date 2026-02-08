import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import ScalarFormatter
import numpy as np

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'figure.titlesize': 16
})

def plot_vertical_weak_scaling(file_path):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"File '{file_path}' non trovato.")
        return

    df = df.sort_values('procs')
    

    df['ratio_avg'] = df['avg_vol'] / df['avg_load']
    df['ratio_min'] = df['min_vol'] / df['avg_load']
    df['ratio_max'] = df['max_vol'] / df['avg_load']

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    ax1.plot(df['procs'], df['ratio_avg'], marker='o', color='#0d1161', 
             linewidth=2.5, label='Avg / Load', zorder=10)
    
    ax1.fill_between(df['procs'], df['ratio_min'], df['ratio_max'], 
                     color='#0d1161', alpha=0.2, label='Min-Max Range', zorder=5)
    
    ax1.plot(df['procs'], df['ratio_min'], color='#0d1161', linestyle=':', alpha=0.5, linewidth=1)
    ax1.plot(df['procs'], df['ratio_max'], color='#0d1161', linestyle=':', alpha=0.5, linewidth=1)

    ax1.set_xscale('log', base=2)
    ax1.set_xticks(sorted(df['procs'].unique()))
    ax1.get_xaxis().set_major_formatter(ScalarFormatter())
    ax1.minorticks_off()
    
    ax1.set_title('Normalized Comm. vol per load unit', fontweight='bold')
    ax1.set_ylabel('Cnorm per rank')
    ax1.grid(True, linestyle='--', alpha=0.3)
    ax1.legend(loc='upper left', frameon=True, framealpha=0.9)
    
    x = np.arange(len(df))
    width = 0.25
    
    color_min = '#fee6ce'   
    color_avg = '#fdae6b'   
    color_max = '#e6550d'   
    
    rects1 = ax2.bar(x - width, df['min_mem_KB'], width, label='Min', 
                     color=color_min, edgecolor='grey', linewidth=0.5)
    
    rects2 = ax2.bar(x, df['avg_mem_KB'], width, label='Avg', 
                     color=color_avg, edgecolor='grey', linewidth=0.5)
    
    rects3 = ax2.bar(x + width, df['max_mem_KB'], width, label='Max', 
                     color=color_max, edgecolor='grey', linewidth=0.5)

    ax2.set_xticks(x)
    ax2.set_xticklabels(df['procs'].astype(str))
    
    ax2.set_title('Memory footprint per rank', fontweight='bold')
    ax2.set_xlabel('Processes')
    ax2.set_ylabel('KB per rank')
    ax2.grid(True, axis='y', linestyle='--', alpha=0.3, zorder=0)
    
    ax2.legend(loc='upper left', frameon=True, framealpha=0.9, title=None)

    output_filename = 'plots/weak_scaling_vertical_mem.png'
    plt.tight_layout()
    plt.savefig(output_filename, dpi=300, bbox_inches='tight', pad_inches=0.1)
    print(f"Grafico salvato: {output_filename}")

plot_vertical_weak_scaling('result/weak_test.csv')