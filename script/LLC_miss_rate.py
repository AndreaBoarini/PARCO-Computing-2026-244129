import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Carica il dataset
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


# 1. Pulizia e Preparazione Dati
# Sostituisce la stringa 'Nan' (che assume essere single-threaded) con '1'
df['thread_option'] = df['thread_option'].replace('Nan', '1')

# Converte thread_option in numerico (integer)
df['thread_option'] = pd.to_numeric(df['thread_option'], errors='coerce').astype(int)

# 2. Calcola LLC Miss Rate percentuale
# LLC Miss Rate = (LLC_misses / LLC_loads) * 100
df['LLC_Miss_Rate'] = np.where(df['LLC_loads'] > 0, (df['LLC_misses'] / df['LLC_loads']) * 100, 0)

# 3. Raggruppa i dati: Calcola la media del LLC Miss Rate per matrice e numero di thread
# Questo media gli effetti di altre opzioni (chunk size, scheduling)
plot_data = df.groupby(['matrix_name', 'nz', 'thread_option'])['LLC_Miss_Rate'].mean().reset_index()

# 4. Determina l'ordine delle matrici (dalla più piccola alla più grande per 'nz')
matrix_order = plot_data[['matrix_name', 'nz']].drop_duplicates().sort_values(by='nz')['matrix_name'].tolist()

# 5. Genera il Plot
plt.figure(figsize=(10, 6))

# Itera sulle matrici nell'ordine determinato e traccia la linea
for matrix in matrix_order:
    matrix_data = plot_data[plot_data['matrix_name'] == matrix]
    # Ordina per thread_option per garantire la corretta sequenza sull'asse x
    matrix_data = matrix_data.sort_values(by='thread_option')

    # Traccia la linea
    plt.plot(matrix_data['thread_option'], matrix_data['LLC_Miss_Rate'], marker='o', label=matrix)

# Personalizzazione del grafico
plt.title('LLC Miss Rate vs. thread number', fontsize=14)
plt.xlabel('Thread Number', fontsize=12)
plt.ylabel('LLC Miss Rate (%)', fontsize=12)

# Imposta i tick dell'asse x solo sui conteggi di thread effettivi
unique_threads = sorted(plot_data['thread_option'].unique())
plt.xticks(unique_threads)

plt.ylim(ymin=0)
plt.legend(title='Matrix (smaller to bigger)', loc='lower right')
plt.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()

# Salva il grafico
plt.savefig("plots/llc_miss_rate_vs_threads.png")