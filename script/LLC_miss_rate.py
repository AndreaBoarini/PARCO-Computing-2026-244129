import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

df = pd.read_csv("results/final_results_cache.csv")

plt.rcParams.update({
    'font.size': 14,           
    'axes.titlesize': 18,      
    'axes.labelsize': 16,      
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'legend.fontsize': 14,
    'legend.title_fontsize': 16
})

df['thread_option'] = df['thread_option'].replace('Nan', '1')

df['thread_option'] = pd.to_numeric(df['thread_option'], errors='coerce').astype(int)

df['LLC_Miss_Rate'] = np.where(df['LLC_loads'] > 0, (df['LLC_misses'] / df['LLC_loads']) * 100, 0)

plot_data = df.groupby(['matrix_name', 'nz', 'thread_option'])['LLC_Miss_Rate'].mean().reset_index()

matrix_order = plot_data[['matrix_name', 'nz']].drop_duplicates().sort_values(by='nz')['matrix_name'].tolist()

plt.figure(figsize=(10, 6))

for matrix in matrix_order:
    matrix_data = plot_data[plot_data['matrix_name'] == matrix]

    matrix_data = matrix_data.sort_values(by='thread_option')

    plt.plot(matrix_data['thread_option'], matrix_data['LLC_Miss_Rate'], marker='o', label=matrix)

plt.title('LLC Miss Rate vs. thread number', fontsize=14)
plt.xlabel('Thread Number', fontsize=12)
plt.ylabel('LLC Miss Rate (%)', fontsize=12)

unique_threads = sorted(plot_data['thread_option'].unique())
plt.xticks(unique_threads)

plt.ylim(ymin=0)
plt.legend(title='Matrix (smaller to bigger)', loc='lower right')
plt.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()

plt.savefig("plots/llc_miss_rate_vs_threads.png")