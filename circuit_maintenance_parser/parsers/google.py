"""Google parser."""

import logging
import re
from datetime import datetime

from circuit_maintenance_parser.parser import CircuitImpact, EmailSubjectParser, Html, Impact, Status

# pylint: disable=too-many-nested-blocks, too-many-branches

logger = logging.getLogger(__name__)


class HtmlParserGoogle1(Html):
    """Notifications Parser for Google notifications."""

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        data["circuits"] = []
        end_time_explicit = False

        for span in soup.find_all("span"):
            if span.string is None:
                continue
            if span.string.strip() == "Start Time:":
                dt_str = span.next_sibling.string.strip()
                data["start"] = self.dt2ts(datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S %z UTC"))
            elif span.string.strip() == "End Time:":
                dt_str = span.next_sibling.string.strip()
                data["end"] = self.dt2ts(datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S %z UTC"))
                end_time_explicit = True
            elif span.string.strip() == "Peer ASN:":
                data["account"] = span.parent.next_sibling.string.strip()
            elif span.string.strip() == "Google Neighbor Address(es):":
                googleaddr = span.parent.next_sibling.string.strip()
            elif span.string.strip() == "Peer Neighbor Address(es):":
                cid = googleaddr + "-" + span.parent.next_sibling.string.strip()
                data["circuits"].append(CircuitImpact(circuit_id=cid, impact=Impact.OUTAGE))

        # Google sometimes send notifications without End Time specificed
        if not end_time_explicit and data["start"]:
            # Since start and end times cannot be equal, manufacturing end date by adding 1hr to start date
            end_time_delta = 3600
            data["end"] = data["start"] + end_time_delta

        return [data]


class SubjectParserGoogle1(EmailSubjectParser):
    """Subject Parser for Google notifications."""

    def parse_subject(self, subject):
        """Parse the subject line."""
        data = {}

        # Example subject format - "[Scheduled] Google Planned Network Maintenance Notification - Reference PCR/123456"
        # Group 1: Status (e.g., Scheduled, Completed, Canceled)
        # Group 2: Maintenance ID (e.g., PCR/123456)
        match = re.search(r"(\[\S+\]).*Reference\s+(\S+)", subject, re.IGNORECASE | re.DOTALL)
        match_2 = re.search(r"\[\S+\]\s+(.*)", subject, re.IGNORECASE | re.DOTALL)

        if match:
            status_str = match.group(1).upper()
            data["maintenance_id"] = match.group(2).strip()
            if "COMPLETED" in status_str:
                data["status"] = Status.COMPLETED
            # To handle both Cancelled and Canceled spelling options just in case
            elif "CANCEL" in status_str:
                data["status"] = Status.CANCELLED
            elif "SCHEDULED" in status_str:
                data["status"] = Status.CONFIRMED
            # If unable to match, we fallback to default confirmed
            else:
                data["status"] = Status.CONFIRMED
        if match_2:
            data["summary"] = match_2.group(1)

        return [data]
