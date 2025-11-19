import pandas as pd
import numpy as np

# Compute 90th percentile on blocks of 10
def compute_block_percentile90(group):
    # Computes the 90th percentile of execution time in blocks of 10 measurements.
    results = []
    rows = group.shape[0]
    for i in range(0, rows, 10):
        block = group.iloc[i:i+10]
        if len(block) == 10:
            p90 = np.percentile(block["exec_time"], 90, method='lower')
            
            # Retrieve the necessary metadata columns from the first row of the block
            row_data = block.iloc[0][[
                "matrix_name", "compiler_option", "thread_option",
                "chunk_size_option", "scheduling_option"
            ]].to_dict()
            
            # Add the calculated percentile
            row_data["p90_exec_time"] = p90
            results.append(row_data)
            
    return pd.DataFrame(results)

def preprocess_csv(df):
    # Correct NaN string values
    df = df.replace({"Nan": np.nan, "NaN": np.nan})

    # Convert columns to appropriate integer types
    integer_cols = [
        "rows", "cols", "nz",
        "thread_option", "chunk_size_option"
    ]

    print("Starting type conversion...")
    for col in integer_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].astype('Int64')
    print("Type conversion complete.")

    # Sort data for better analysis
    df_sorted = df.sort_values([
        "matrix_name", "compiler_option", "thread_option",
        "chunk_size_option", "scheduling_option"
    ])

    # Apply the 90th percentile calculation for each combination
    df_90_perc = df_sorted.groupby([
        "matrix_name", "compiler_option",
        "thread_option", "chunk_size_option",
        "scheduling_option"
    ], dropna=False, group_keys=False).apply(compute_block_percentile90).reset_index(drop=True)

    return df_90_perc