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
import requests
from flask import Flask, Response, request
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Mapping of Windows timezone names to IANA timezone names
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
    # Add more mappings as needed
}


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
