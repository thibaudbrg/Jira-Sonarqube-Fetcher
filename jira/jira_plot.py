import os
import json
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import warnings
from colorama import init, Fore, Style

# Initialize colorama to make ANSI escape character sequences work 
# under MS Windows terminals
init(autoreset=True)

# Suppress seaborn FutureWarnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def parse_args():
    parser = argparse.ArgumentParser(
        description=f"{Fore.CYAN}Advanced Analysis of Work Log Data",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Increase output verbosity for more detailed logging.")
    return parser.parse_args()

args = parse_args()

def load_data(directory='./data'):
    if args.verbose:
        print(f"{Fore.GREEN}Loading data from {directory}...")
    all_data = []
    for folder in sorted(os.listdir(directory)):
        folder_path = os.path.join(directory, folder)
        if os.path.isdir(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith('.json'):
                    with open(os.path.join(folder_path, file), 'r') as f:
                        data = json.load(f)
                        all_data.extend(data)
    if args.verbose:
        print(f"{Fore.BLUE}Data loaded successfully.")
    return pd.DataFrame(all_data)

def save_plot(figure, filename):
    plot_dir = 'plots'
    if not os.path.exists(plot_dir):
        os.makedirs(plot_dir)
    figure.savefig(os.path.join(plot_dir, filename))
    plt.close(figure)
    print(f"{Fore.YELLOW}Plot saved: {filename}")

def calculate_average_time(df):
    df['worklog_start'] = pd.to_datetime(df['worklog_start'], errors='coerce', utc=True)
    if df['worklog_start'].isnull().any():
        print("Warning: Some 'worklog_start' values could not be converted to datetime.")
    df['worklog_start'] = df['worklog_start'].dt.tz_convert(None)
    df['month'] = df['worklog_start'].dt.to_period('M').astype(str)
    df['time_spent_seconds'] = pd.to_numeric(df['time_spent_seconds'], errors='coerce')
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(subset=['time_spent_seconds'], inplace=True)
    avg_time_per_issue = df.groupby(['user_name', 'month'])['time_spent_seconds'].mean().reset_index()
    avg_time_per_issue['time_spent_hours'] = avg_time_per_issue['time_spent_seconds'] / 3600
    return avg_time_per_issue

def plot_avg_time_spent(avg_time_df):
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.lineplot(data=avg_time_df, x='month', y='time_spent_hours', hue='user_name', marker='o', ax=ax)
    plt.title('Average Time Spent per Issue by Month')
    plt.xlabel('Month')
    plt.ylabel('Average Time Spent (hours)')
    plt.xticks(rotation=45)
    plt.legend(title='Tester', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    save_plot(fig, 'avg_time_spent_per_issue_by_month.png')

def plot_total_time_spent_per_tester(df):
    # Ensure 'time_spent_hours' is calculated
    if 'time_spent_hours' not in df.columns:
        df['time_spent_hours'] = df['time_spent_seconds'] / 3600
    
    # Aggregate total time spent per tester per month
    df_total_time = df.groupby(['user_name', 'month'], as_index=False)['time_spent_hours'].sum()
    df_total_time.rename(columns={'time_spent_hours': 'total_time_spent_hours'}, inplace=True)
    
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.barplot(data=df_total_time, x='month', y='total_time_spent_hours', hue='user_name', ax=ax)
    plt.title('Total Time Spent per Tester by Month')
    plt.xlabel('Month')
    plt.ylabel('Total Time Spent (hours)')
    plt.xticks(rotation=45)
    plt.legend(title='Tester', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    save_plot(fig, 'total_time_spent_per_tester_by_month.png')

def plot_issues_per_tester_by_month(df):
    fig, ax = plt.subplots(figsize=(14, 8))
    issue_counts = df.groupby(['user_name', 'month'])['issue_key'].nunique().reset_index(name='issue_count')
    sns.lineplot(data=issue_counts, x='month', y='issue_count', hue='user_name', marker='o', ax=ax)
    plt.title('Number of Issues Handled Per Tester by Month')
    plt.xlabel('Month')
    plt.ylabel('Number of Issues')
    plt.xticks(rotation=45)
    plt.legend(title='Tester', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    save_plot(fig, 'issues_per_tester_by_month.png')

def plot_avg_time_all_testers(df):
    fig, ax = plt.subplots(figsize=(10, 6))
    avg_time = df.groupby('month')['time_spent_seconds'].mean().reset_index()
    avg_time['time_spent_hours'] = avg_time['time_spent_seconds'] / 3600
    sns.lineplot(data=avg_time, x='month', y='time_spent_hours', marker='o', ax=ax)
    plt.title('Average Time Spent on Issues Each Month (All Testers Combined)')
    plt.xlabel('Month')
    plt.ylabel('Average Time Spent (hours)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    save_plot(fig, 'avg_time_all_testers_each_month.png')

def plot_time_spent_distribution(df):
    # Check if the DataFrame is empty or if 'time_spent_hours' does not exist
    if df.empty or 'time_spent_hours' not in df.columns:
        print(f"{Fore.RED}DataFrame is empty or 'time_spent_hours' column is missing.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(df, x='time_spent_hours', bins=30, kde=True, ax=ax)
    plt.title('Distribution of Time Spent on Issues')
    plt.xlabel('Time Spent (hours)')
    plt.ylabel('Frequency')
    plt.tight_layout()
    save_plot(fig, 'distribution_of_time_spent_on_issues.png')




def main():
    if args.verbose:
        print(f"{Fore.CYAN}Verbose mode enabled. Starting analysis...")
    df = load_data()
    
    if df.empty:
        print(f"{Fore.RED}No data found. Exiting.")
        return

    df = load_data()  # Load your data
    # Ensure 'time_spent_hours' is calculated for the entire DataFrame
    df['time_spent_seconds'] = pd.to_numeric(df['time_spent_seconds'], errors='coerce', downcast='float')
    df['time_spent_hours'] = df['time_spent_seconds'] / 3600

    # Additional check or transformation if needed
    if 'time_spent_hours' not in df.columns or df.empty:
        print("'time_spent_hours' column missing or DataFrame is empty. Check data loading and processing steps.")
        return
    
    avg_time_per_issue = calculate_average_time(df)
    plot_avg_time_spent(avg_time_per_issue)
    plot_total_time_spent_per_tester(df)
    plot_issues_per_tester_by_month(df)
    plot_avg_time_all_testers(df)
    plot_time_spent_distribution(df)

    if args.verbose:
        print(f"{Fore.GREEN}Data analysis completed successfully.")


if __name__ == "__main__":
    main()