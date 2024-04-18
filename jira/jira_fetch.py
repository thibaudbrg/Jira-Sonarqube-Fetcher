import argparse
import os
import json
import requests
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from colorama import init, Fore, Style
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Initialize colorama
init(autoreset=True)


# Enhanced logging configuration
logging.basicConfig(level=logging.INFO, format=f'%(asctime)s - %(levelname)s - {Fore.BLUE}%(message)s{Style.RESET_ALL}')

# Authentication details and Jira URL setup from .env file
PAT = os.getenv('PAT')
JIRA_SEARCH_URL = os.getenv('JIRA_SEARCH_URL')
HEADERS = {"Accept": "application/json", "Authorization": f"Bearer {PAT}"}

def parse_args():
    parser = argparse.ArgumentParser(description=f"{Fore.YELLOW}Advanced Jira Data Fetcher for GitHub Copilot KPI Analysis{Style.RESET_ALL}",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-m", "--months", type=int, default=6, help="Number of months back to fetch data for.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging.")
    return parser.parse_args()

def load_testers_config(config_path='testers_config.json'):
    try:
        with open(config_path, 'r') as config_file:
            testers = json.load(config_file)
        return testers
    except FileNotFoundError:
        logging.error(f"{Fore.RED}Testers configuration file not found: {config_path}")
        exit()

def generate_email(name, ext):
    firstname, surname = name.split()
    domain = "@ext.ubp.ch" if ext else "@ubp.ch"
    return f"{firstname.lower()}.{surname.lower()}{domain}"

def extract_relevant_info(data):
    relevant_info = []
    for issue in data.get('issues', []):
        worklogs = issue.get('fields', {}).get('worklog', {}).get('worklogs', [])
        for worklog in worklogs:
            info = {
                'user_name': worklog.get('author', {}).get('displayName'),
                'user_email': worklog.get('author', {}).get('emailAddress'),
                'issue_key': issue.get('key'),
                'issue_id': issue.get('id'),
                'worklog_id': worklog.get('id'),
                'time_spent_seconds': worklog.get('timeSpentSeconds'),
                'worklog_start': worklog.get('started'),
            }
            relevant_info.append(info)
        timetracking = issue.get('fields', {}).get('timetracking', {})
        if timetracking:
            info.update({
                'original_estimate_seconds': timetracking.get('originalEstimateSeconds'),
                'remaining_estimate_seconds': timetracking.get('remainingEstimateSeconds'),
                'time_spent_seconds': timetracking.get('timeSpentSeconds')
            })
    return relevant_info

def save_data_to_file(folder_name, filename, data):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    file_path = os.path.join(folder_name, filename)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    logging.info(f"Data saved to {file_path}")

def fetch_and_process_issues_for_tester(tester, start_date, end_date):
    email = generate_email(tester["name"], tester["ext"])
    jql_query = f"assignee=\"{email}\" AND worklogDate >= '{start_date}' AND worklogDate <= '{end_date}'"
    params = {"jql": jql_query, "fields": "timetracking,worklog", "maxResults": 1000}

    # Use the correct global variable names here
    response = requests.get(JIRA_SEARCH_URL, headers=HEADERS, params=params, verify="../cert.cer")  # or the correct path to your certificate
    if response.status_code == 200:
        search_results = response.json()
        extracted_info = extract_relevant_info(search_results)
        if extracted_info:
            folder_name = f"data/{end_date}"
            filename = f"data_{tester['trigram']}-{end_date}.json"
            save_data_to_file(folder_name, filename, extracted_info)
    else:
        logging.error(f"Failed to fetch issues for {tester['name']}. Status code: {response.status_code}")


def fetch_data_for_period(months_back, testers):
    today = datetime.today()
    for i in range(months_back, -1, -1):
        start_date = (today - relativedelta(months=i)).replace(day=1).strftime('%Y-%m-%d')
        end_date = (today - relativedelta(months=i-1, days=1)).strftime('%Y-%m-%d') if i != 0 else today.strftime('%Y-%m-%d')
        for tester in testers:
            fetch_and_process_issues_for_tester(tester, start_date, end_date)

def main():
    args = parse_args()

    # Set logging level based on verbose flag
    logging_level = logging.DEBUG if args.verbose else logging.INFO
    logging.getLogger().setLevel(logging_level)

    # Load testers configuration
    testers = load_testers_config()

    months_back = args.months

    # Validate the 'months' argument
    if months_back < 1:
        logging.error(f"{Fore.RED}The --months argument must be a positive integer.")
        return

    logging.info(f"{Fore.GREEN}Fetching data for the past {months_back} months...")

    # Fetch and process data for the specified period
    fetch_data_for_period(months_back, testers)

if __name__ == "__main__":
    main()