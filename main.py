#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "flask<3",
#   "requests<3",
#   "python-dotenv<2"
# ]
# ///

import re
import os
import sys
import requests
from flask import Flask, Response, request
import logging
from dotenv import load_dotenv
import csv
from collections import defaultdict

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

def load_timezone_mappings(csv_file_path):
    """
    Load timezone mappings from a CSV file.

    Format of the CSV:
    Windows_Timezone, Territory, IANA_Timezone

    Returns a dictionary mapping Windows timezone names to IANA timezone names.
    """
    timezone_mapping = {}

    # We'll use a temporary dictionary to collect all IANA timezones for each Windows timezone
    temp_mapping = defaultdict(set)

    with open(csv_file_path, 'r') as csvfile:
        csv_reader = csv.reader(csvfile)
        for row in csv_reader:
            if len(row) < 3:
                continue

            windows_tz = row[0].strip()
            territory = row[1].strip()
            iana_tzs = row[2].strip().split()

            # Add all IANA timezones for this Windows timezone
            for iana_tz in iana_tzs:
                temp_mapping[windows_tz].add(iana_tz)

    # Process the collected timezones
    for windows_tz, iana_tzs in temp_mapping.items():
        # We prioritize any timezone with 'Europe' or a major city in its name for better readability
        priority_tzs = [tz for tz in iana_tzs if 'Europe' in tz or any(city in tz for city in ['Berlin', 'Paris', 'London', 'Rome', 'Madrid'])]

        if priority_tzs:
            # Use the first priority timezone
            timezone_mapping[windows_tz] = priority_tzs[0]
        else:
            # If no priority timezone, use the first one in the set
            timezone_mapping[windows_tz] = next(iter(iana_tzs))

    return timezone_mapping

# Try to load timezone mappings from CSV
csv_path = os.path.join(os.path.dirname(__file__), 'timezone.csv')
try:
    TIMEZONE_MAPPING = load_timezone_mappings(csv_path)
    logging.info(f"Loaded {len(TIMEZONE_MAPPING)} timezone mappings from {csv_path}")
except Exception as e:
    logging.warning(f"Failed to load timezone mappings from {csv_path}: {e}")
    # Fallback to hardcoded mappings
    TIMEZONE_MAPPING = {
        "Central Europe Standard Time": "Europe/Berlin",
        "W. Europe Standard Time": "Europe/Berlin",
        "Romance Standard Time": "Europe/Paris",
        "GMT Standard Time": "Europe/London",
        "E. Europe Standard Time": "Europe/Bucharest",
        "Eastern Standard Time": "America/New_York",
        "Pacific Standard Time": "America/Los_Angeles",
        "Central Standard Time": "America/Chicago",
        "Mountain Standard Time": "America/Denver",
        "AUS Eastern Standard Time": "Australia/Sydney",
        "Tokyo Standard Time": "Asia/Tokyo",
        "China Standard Time": "Asia/Shanghai",
    }
    logging.info("Using fallback timezone mappings")


def fix_ical_timezones(ical_content):
    """
    Fix TZID entries in iCal content from Outlook format to standard IANA format
    """
    for outlook_tz, iana_tz in TIMEZONE_MAPPING.items():
        # Case 1: Fix standalone TZID property (TZID:W. Europe Standard Time)
        ical_content = re.sub(
            r"TZID:" + re.escape(outlook_tz), f"TZID:{iana_tz}", ical_content
        )

        # Case 2: Fix standalone TZID parameters (TZID="W. Europe Standard Time")
        ical_content = re.sub(
            r'TZID="?' + re.escape(outlook_tz) + r'"?', f"TZID={iana_tz}", ical_content
        )

        # Case 3: Fix TZID when part of multiple parameters (;TZID="W. Europe Standard Time")
        ical_content = re.sub(
            r'(;TZID="?)' + re.escape(outlook_tz) + r'("?)',
            f"\\1{iana_tz}\\2",
            ical_content,
        )

    return ical_content


@app.route("/proxy")
def proxy_ical():
    """
    Proxy endpoint that fetches an iCal file and fixes its timezone identifiers
    """
    # Get the URL parameter
    ical_url = request.args.get("url")

    if not ical_url:
        return "Missing parameter", 400

    try:
        # Fetch the iCal file from the provided URL
        response = requests.get(ical_url)
        response.raise_for_status()

        # Fix the timezone identifiers
        fixed_ical = fix_ical_timezones(response.text)

        # Return the fixed iCal file with appropriate headers
        return Response(
            fixed_ical,
            mimetype="text/calendar",
            headers={"Content-Disposition": "attachment; filename=calendar.ics"},
        )

    except requests.RequestException as e:
        logging.error(f"Error fetching iCal: {e}")
        return f"Error fetching iCal file: {str(e)}", 500


if __name__ == "__main__":
    # Set up logging
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(level=getattr(logging, log_level))

    # Get port from environment variable or command line
    port = int(os.getenv('PORT', sys.argv[1] if len(sys.argv) > 1 else 5000))

    # Get host from environment variable
    host = os.getenv('HOST', '0.0.0.0')

    print(f"Starting iCal proxy server on port {port}")
    print(f"Use: http://localhost:{port}/proxy?url=YOUR_ICAL_URL")

    app.run(host=host, port=port)
