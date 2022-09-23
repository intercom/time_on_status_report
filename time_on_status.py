import os
import sys
import csv
import requests
import click
from humanize import precisedelta
from datetime import datetime, timedelta

TOKEN = os.environ.get('INTERCOM_API_TOKEN')

def dates_between(s, e):
    num_days = (e - s).days
    dates = []
    for x in range(num_days):
        dates.append(s + timedelta(days=x))
    return dates


class AwayModeUpdate:
    def __init__(self, log):
        self.admin_id = log['performed_by']['id']
        self.admin_email = log['performed_by']['email']
        self.away = log['metadata']['away_mode']
        self.reassigning = log['metadata']['reassign_conversations']
        self.created_at = datetime.fromtimestamp(log['created_at'])

    @property
    def status(self):
        if self.away and not self.reassigning:
            return 'away'
        elif self.away and self.reassigning:
            return 'reassigning'
        else:
            return 'active'

    def __repr__(self):
        return f'{self.admin_email} - {self.status} at {self.created_at}'

class Admin:
    def __init__(self, admin_id, email):
        self.admin_id = admin_id
        self.email = email
        self.periods = []

    def set_status(self, update):
        if self.periods:
            self.periods[-1].end = update.created_at

        self.periods.append(StatusPeriod(update.created_at, None, update.status))

    def __repr__(self):
        return f'{self.email}'

class StatusPeriod:
    def __init__(self, start, end, status):
        self.start = start
        self.end = end
        self.status = status

    def duration_on_date(self, date):
        date_start = date
        date_end = date + timedelta(days=1)

        if (self.end is not None and self.end < date_start) or self.start >= date_end:
            return timedelta(seconds=0)

        duration_start = max(self.start, date_start)

        if self.end is None:
            duration_end = date_end
        else:
            duration_end = min(self.end, date_end)

        return duration_end - duration_start

    def __repr__(self):
        return f'{self.status} from {self.start} to {self.end}'

def fetch_activity_logs(token, start, end):
    HEADERS = {
        'Authorization': f'Bearer {token}',
        'accept': 'application/json'
    }

    URL = 'https://api.intercom.io/admins/activity_logs'
    params = {
        'created_at_after': start.timestamp(),
        'created_at_before': end.timestamp(),
    }
    logs = []
    next_url = URL
    while next_url:
        click.echo('fetching data...')
        resp = requests.get(next_url, params=params, headers=HEADERS)
        data = resp.json()
        if resp.status_code != 200:
            click.echo(f'Something went wrong will fetching the data - {resp.status_code}: {resp.reason}')
            sys.exit(1)

        next_url = data['pages']['next']
        logs.extend(data['activity_logs'])
    click.echo('finished fetching data')
    return logs

def parse_away_logs(away_logs):
    admins = {}
    for log in away_logs:
        if log.admin_email not in admins:
            admins[log.admin_email] = Admin(log.admin_id, log.admin_email)
        admin = admins[log.admin_email]
        admin.set_status(log)

    return admins

def compile_time_on_status(admins, dates):
    time_on_status = {}
    for email, admin in admins.items():
        time_on_status[email] = {}
        for d in dates:
            time_on_status[email][d] = { 'away': timedelta(seconds=0), 'reassigning': timedelta(seconds=0), 'active': timedelta(seconds=0) }
            for p in admin.periods:
                time_on_status[email][d][p.status] += p.duration_on_date(d)

    return time_on_status

def write_csv(data, filename):
    header = [
        'Teammate Email',
        'Date (UTC)',
        'Status',
        'Time on status'
    ]
    with open(filename, mode="w", newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter='\t', quotechar='|')
        writer.writerow(header)
        for admin_email, b in data.items():
            for event_date, d in b.items():
                for status_type, time_on in d.items():
                    writer.writerow([admin_email, event_date, status_type, precisedelta(time_on, suppress=['days'])])

@click.command()
@click.argument('start_date')
@click.argument('end_date')
@click.argument('intercom_api_token', envvar="INTERCOM_API_TOKEN")
def generate_report(start_date, end_date, intercom_api_token):
    """ Generates a csv file reporting time on status for all teammates that had any activity during the specified time window.

        START_DATE: 'Date to start the search from (inclusive). Must be of the format YYYY-MM-DD (e.g. 2022-06-01)'

        END_DATE: 'Date to start the search from (exclusive). Must be of the format YYYY-MM-DD (e.g. 2022-07-01)'

        INTERCOM_API_TOKEN: The access token you get from the developer hub from your intercom workspace.
        See https://developers.intercom.com/building-apps/docs/authentication-types#section-access-tokens for more details on how to get one.
        You can specify this argument as an environment variable also (e.g. export INTERCOM_API_TOKEN=<some-token>).
    """
    expected_date_format = '%Y-%m-%d'
    search_start_date = datetime.strptime(start_date, expected_date_format)
    search_end_date = datetime.strptime(end_date, expected_date_format)

    click.echo(f'Generating time on status report for {search_start_date} to {search_end_date}')

    logs = fetch_activity_logs(intercom_api_token, search_start_date, search_end_date)
    away_logs = [AwayModeUpdate(l) for l in logs  if l['activity_type'] == 'admin_away_mode_change']
    away_logs = sorted(away_logs, key=lambda x: x.created_at)

    admins = parse_away_logs(away_logs)
    dates = dates_between(search_start_date, search_end_date)
    time_on_status = compile_time_on_status(admins, dates)
    filename = f'time_on_status_report_for_{search_start_date.strftime(expected_date_format)}_to_{search_end_date.strftime(expected_date_format)}.csv'
    click.echo(f'writing report to {click.format_filename(filename)}')
    write_csv(time_on_status, filename)
    click.echo('FINISHED!')
