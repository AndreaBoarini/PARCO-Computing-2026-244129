import pandas as pd
import numpy as np

def compute_block_percentile90(group):
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