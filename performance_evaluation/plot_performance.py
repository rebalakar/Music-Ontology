import sys
import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from src.main import main as run_pipeline

def run_multiple_pipelines(num_runs=5):
    runs = []
    for i in range(num_runs):
        print(f"\n--- Run {i+1}/{num_runs} ---")
        metrics = run_pipeline() 
        runs.append(metrics)
    return runs

def create_metrics_dataframe(runs):
    # Create a DataFrame from the list of dictionaries
    df = pd.DataFrame(runs)
    # Compute a row of averages for all numeric columns
    average_row = df.mean(numeric_only=True)
    average_row = pd.DataFrame(average_row).transpose()
    average_row.index = ['Average']
    # Append the average row to the DataFrame
    df = pd.concat([df, average_row])
    return df

def save_metrics_table(df, csv_filename="performance_metrics.csv", img_filename="performance_table.png"):
    # Save DataFrame to a CSV file
    df.to_csv(csv_filename, index_label="Run")
    print(f"Saved performance metrics to '{csv_filename}'")
    
    # Create a matplotlib figure to display the table
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis('tight')
    ax.axis('off')
    
    # Round numeric values for clarity
    rounded_values = np.round(df.values, 2)
    
    # Create a table from the DataFrame values
    table = ax.table(
        cellText=rounded_values,
        colLabels=df.columns,
        rowLabels=df.index,
        loc="center"
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    
    fig.tight_layout()
    plt.savefig(img_filename)
    print(f"Saved performance metrics table as image '{img_filename}'")

def main():
    # Decide whether to use a warmup run or to measure memory usage from cold start
    cold_start = False
    
    if cold_start:
        num_runs = 1
    else:
        print('Warmup run...')
        run_pipeline()
        num_runs = 5

    runs = run_multiple_pipelines(num_runs)
    
    # Create a DataFrame containing all runs plus a row for averages
    df = create_metrics_dataframe(runs)
    print("\n--- All Run Metrics and Averages ---")
    print(df)
    
    # Save the DataFrame as both CSV and a table image
    save_metrics_table(df)

if __name__ == "__main__":
    main()