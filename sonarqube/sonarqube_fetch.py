import argparse
import requests
import base64
import os
import json
from datetime import datetime, timedelta
import logging
from colorama import Fore, Style, init
from dotenv import load_dotenv

# Initialize colorama for colored output and load environment variables
init(autoreset=True)
load_dotenv()

# Setup command line argument parsing
parser = argparse.ArgumentParser(description="Fetch and save SonarQube project data.")
parser.add_argument("-v", "--verbose", help="Increase output verbosity", action="store_true")
parser.add_argument("-m", "--month", type=int, default=12, help="Number of months back to fetch data for")
args = parser.parse_args()

# Set logging level based on verbosity argument
logging_level = logging.DEBUG if args.verbose else logging.INFO
logging.basicConfig(level=logging_level, format=f"{Fore.YELLOW}%(asctime)s{Style.RESET_ALL} - %(levelname)s - {Fore.LIGHTGREEN_EX}%(message)s{Style.RESET_ALL}")

# Initialize the data directory
data_directory = "./data"
if not os.path.exists(data_directory):
    os.makedirs(data_directory)
    logging.info(f"Created directory: {data_directory}")

# SonarQube server details and API token
API_TOKEN = os.getenv("SONARQUBE_API_TOKEN")
SONARQUBE_URL = os.getenv("SONARQUBE_URL")
headers = {"Authorization": f"Basic {base64.b64encode(f'{API_TOKEN}:'.encode('ascii')).decode('ascii')}"}

# Metrics to analyze and the start date based on the number of months specified
metrics = "coverage,bugs,vulnerabilities,code_smells,ncloc,sqale_index"
start_date = (datetime.now() - timedelta(days=30*args.month)).strftime('%Y-%m-%d')
project_keys = ["OMS", "nit", "ubp.dione.esignature", "secli_oracle", "PortailGerants_IT_TOOLING_filter", "Ubp.Dione.UserEnrollment"]

def save_json(data, filename):
    path = os.path.join(data_directory, f"{filename}.json")
    with open(path, 'w') as file:
        json.dump(data, file, indent=4)
    logging.info(f"{Fore.CYAN}Data saved to {filename}.json")

def fetch_and_save_project_data(project_key):
    for func in [fetch_metrics_for_project, fetch_metrics_history, fetch_issues_detailed]:
        logging.info(f"{Fore.YELLOW}Fetching data with {func.__name__} for project: {project_key}")
        data = func(project_key)
        if data:
            save_json(data, f"{project_key}_{func.__name__}")
        else:
            logging.error(f"{Fore.RED}Failed to fetch data for {project_key} with {func.__name__}")

def fetch_metrics_for_project(project_key):
    try:
        endpoint = f"{SONARQUBE_URL}/api/measures/component"
        params = {"component": project_key, "metricKeys": metrics}
        response = requests.get(endpoint, headers=headers, params=params, verify="../cert.cer")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"{Fore.RED}{e}")
        return None

def fetch_metrics_history(project_key):
    metrics_data = {"project": project_key, "metrics_history": {}}
    for metric in metrics.split(","):
        try:
            endpoint = f"{SONARQUBE_URL}/api/measures/search_history"
            params = {"component": project_key, "metrics": metric, "from": start_date}
            response = requests.get(endpoint, headers=headers, params=params, verify="../cert.cer")
            response.raise_for_status()
            metrics_data["metrics_history"][metric] = response.json().get('measures', [])
        except requests.exceptions.RequestException as e:
            logging.error(f"{Fore.RED}{e}")
    return metrics_data

def fetch_issues_detailed(project_key):
    try:
        endpoint = f"{SONARQUBE_URL}/api/issues/search"
        params = {"componentKeys": project_key, "createdAfter": start_date, "statuses": "OPEN,CONFIRMED,REOPENED", "additionalFields": "_all"}
        response = requests.get(endpoint, headers=headers, params=params, verify="../cert.cer")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"{Fore.RED}{e}")
        return None

def main():
    logging.info("Starting data fetch for projects")
    for project_key in project_keys:
        fetch_and_save_project_data(project_key)
    logging.info("Data fetch completed")

if __name__ == "__main__":
    main()
