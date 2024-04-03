import matplotlib.pyplot as plt
import numpy as np
import json
import os
from datetime import datetime
import logging
from colorama import Fore, Style, init

# Initialize colorama for colored output in terminal and configure logging
init(autoreset=True)
logging.basicConfig(level=logging.INFO, format=f"{Fore.BLUE}%(asctime)s{Style.RESET_ALL} - %(levelname)s - {Fore.GREEN}%(message)s{Style.RESET_ALL}")

plot_directory = "./plots"
data_directory = "./data"

# Ensure the plot directory exists
if not os.path.exists(plot_directory):
    os.makedirs(plot_directory)
    logging.info("Created plot directory.")

def load_json(filename):
    """Loads a JSON file from the specified data directory."""
    try:
        with open(os.path.join(data_directory, f"{filename}.json"), 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error(f"{Fore.RED}File {filename} not found in {data_directory}.")
        return None

def parse_date(entry, field):
    """Parses the creation date of an issue from the JSON data."""
    return datetime.strptime(entry[field], "%Y-%m-%dT%H:%M:%S%z")


def convert_effort_to_minutes(effort_str):
    total_minutes = 0
    # Replace known patterns to ensure consistency in splitting
    effort_str = effort_str.replace('h', 'h ').replace('min', ' min').replace('  ', ' ')
    parts = effort_str.split()

    for part in parts:
        if 'h' in part:
            try:
                # Extract hours and convert to minutes
                hours = int(part.replace('h', ''))
                total_minutes += hours * 60
            except ValueError:
                # Handle cases like 'h' without a number
                continue
        elif 'min' in part:
            try:
                # Directly add minutes
                minutes = int(part.replace('min', ''))
                total_minutes += minutes
            except ValueError:
                # Handle cases like 'min' without a number
                continue

    return total_minutes

def plot_metric_evolution(projects):
    """Plots the evolution of various metrics over time for specified projects,
    with each metric in its own subplot."""
    # Define the metrics of interest
    metrics_of_interest = ['coverage', 'bugs', 'vulnerabilities', 'code_smells', 'ncloc', 'sqale_index']

    # Setup the subplot grid - 3 rows by 2 columns in this case
    fig, axs = plt.subplots(3, 2, figsize=(20, 15))
    fig.suptitle('Metric Evolution Over Time')

    # Flatten the array of axes for easy indexing
    axs = axs.flatten()

    for project in projects:
        metrics_history = load_json(f"{project}_fetch_metrics_history")
        if metrics_history is None:
            continue

        for idx, metric in enumerate(metrics_of_interest):
            if metric in metrics_history['metrics_history']:
                history = metrics_history['metrics_history'][metric]
                all_dates = [item for sublist in history for item in sublist['history']]
                dates = [parse_date(entry, 'date') for entry in all_dates]
                values = [float(entry['value']) for entry in all_dates]
                axs[idx].plot(dates, values, label=f"{project}")
                axs[idx].set_title(metric)
                axs[idx].tick_params(axis='x', rotation=45)
                axs[idx].set_ylabel('Value')
                axs[idx].legend()

    # Adjust layout to make room for the title and x-axis labels
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(f"{plot_directory}/metric_evolution_separated.png")
    plt.close()
    logging.info("Separated metrics evolution plots created.")


def plot_issues_effort(projects):
    """Plots the distribution of issue resolution efforts across projects."""
    plt.figure(figsize=(14, 7))
    for project in projects:
        issues_detailed = load_json(f"{project}_fetch_issues_detailed")
        if issues_detailed is None or 'issues' not in issues_detailed:
            continue
        efforts = [convert_effort_to_minutes(issue['effort']) for issue in issues_detailed['issues'] if 'effort' in issue]
        plt.hist(efforts, bins=30, alpha=0.5, label=project)

    plt.xlabel('Effort (minutes)')
    plt.ylabel('Number of Issues')
    plt.title('Distribution of Issue Resolution Efforts')
    plt.legend()
    plt.savefig(f"{plot_directory}/issue_effort_distribution.png")
    plt.close()
    logging.info("Issue effort distribution plot created.")

def plot_cumulative_effort_over_time(projects):
    """Plots the cumulative effort over time for resolving issues across projects."""
    plt.figure(figsize=(14, 7))
    for project in projects:
        issues_detailed = load_json(f"{project}_fetch_issues_detailed")
        if issues_detailed is None or 'issues' not in issues_detailed:
            continue
        dates = [parse_date(issue, 'creationDate') for issue in issues_detailed['issues'] if 'creationDate' in issue and 'effort' in issue]
        efforts = [convert_effort_to_minutes(issue['effort']) for issue in issues_detailed['issues'] if 'creationDate' in issue and 'effort' in issue]
        dates_sorted_indices = np.argsort(dates)
        dates = np.array(dates)[dates_sorted_indices]
        cumulative_efforts = np.cumsum(np.array(efforts)[dates_sorted_indices])
        plt.plot(dates, cumulative_efforts, label=f"{project}")

    plt.xlabel('Date')
    plt.ylabel('Cumulative Effort (minutes)')
    plt.title('Cumulative Effort Over Time')
    plt.legend()
    plt.savefig(f"{plot_directory}/cumulative_effort_over_time.png")
    plt.close()
    logging.info("Cumulative effort over time plot created.")

def main():
    logging.info("Starting plotting process...")
    projects = ["OMS", "nit", "ubp.dione.esignature", "secli_oracle", "PortailGerants_IT_TOOLING_filter", "Ubp.Dione.UserEnrollment"]
    plot_metric_evolution(projects)
    plot_issues_effort(projects)
    plot_cumulative_effort_over_time(projects)
    logging.info("Plotting process completed.")

if __name__ == "__main__":
    main()
