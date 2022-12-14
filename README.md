# Time on Status Report Generator

## TL;DR
https://www.loom.com/share/d29dd187672f49209d49970e51757dd6

This is a small python program to query the Intercom API for the admin activity logs, and compile the time on each status for the individual teammates in the app.
There are a few caveats with the data generated.
 - Because we infer the time on status from events, we can't know anything about the status of an admin until we see an event, so for all days in the range of days that you search for where an admin changed their status, their time on each status will be reported as 0.
 - Similar to the above, we infer teammates based on the activity events present. Therefore if a teammate does not update their status during the range of days search for, then they won't show up in this report at all.

## Installation
This is configured as a python package.
**WARNING:** I have done absolutely nothing to ensure this code is system agnostic or compatible with any version of python other than 3.10. I used pyenv to install python v3.10.3 and create a virtual environment into which I would install this package and it's dependecies. I'm using a Macbook Pro running macOS Monterey v12.6.
```
cd time_on_status
pip install .
```

## Running

### see the help message
```
generate_time_on_status_report --help
```

### run for a for the months of June, July, and August
```
generate_time_on_status_report 2022-06-01 2022-09-01
```
**Note:** that in order to access the API for your intercom workspace, you need an access token. That token can be passed as a third argument on the command line, or as the environment variable "INTERCOM_API_TOKEN"

## Getting an access token
follow these instructions: https://developers.intercom.com/building-apps/docs/authentication-types#section-access-tokens

## Example Report
See here: https://docs.google.com/spreadsheets/d/19lOO4KzmbteJoR9CZzbaMFGh_31dWx1KMm0IrPkc9kw/edit?usp=sharing
