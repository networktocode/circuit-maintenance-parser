"""Windstream Fiber parser."""
import logging
from datetime import datetime, timezone
import pytz

from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status

# pylint: disable=too-many-nested-blocks, too-many-branches

logger = logging.getLogger(__name__)


class HtmlParserWindstream1(Html):
    """Notifications Parser for Windstream notifications."""

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        data["circuits"] = []
        impact = Impact("NO-IMPACT")
        confirmation_words = [
            "Demand Maintenance Notification",
            "Planned Maintenance Notification",
            "Emergency Maintenance Notification",
        ]
        cancellation_words = ["Postponed Maintenance Notification", "Cancelled Maintenance Notification"]

        h1_tag = soup.find("h1")
        if h1_tag.string.strip() == "Completed Maintenance Notification":
            data["status"] = Status("COMPLETED")
        elif any(keyword in h1_tag.string.strip() for keyword in confirmation_words):
            data["status"] = Status("CONFIRMED")
        elif h1_tag.string.strip() == "Updated Maintenance Notification":
            data["status"] = Status("RE-SCHEDULED")
        elif any(keyword in h1_tag.string.strip() for keyword in cancellation_words):
            data["status"] = Status("CANCELLED")

        div_tag = h1_tag.find_next_sibling("div")
        summary_text = div_tag.get_text(separator="\n", strip=True)
        summary_text = summary_text.split("\nDESCRIPTION OF MAINTENANCE")[0]

        data["summary"] = summary_text

        table = soup.find("table")
        for row in table.find_all("tr"):
            if len(row) < 2:
                continue
            cols = row.find_all("td")
            header_tag = cols[0].string
            if header_tag is None or header_tag == "Maintenance Address:":
                continue
            header_tag = header_tag.string.strip()
            value_tag = cols[1].string.strip()
            if header_tag == "WMT:":
                data["maintenance_id"] = value_tag
            elif "Date & Time:" in header_tag:
                value_tag = value_tag.replace(" ET", "")
                date_obj_est = datetime.strptime(value_tag, "%m/%d/%y %H:%M")
                date_obj_est = pytz.timezone("US/Eastern").localize(date_obj_est)
                if "Event Start" in header_tag:
                    data["start"] = int(date_obj_est.astimezone(pytz.utc).replace(tzinfo=timezone.utc).timestamp())
                elif "Event End" in header_tag:
                    data["end"] = int(date_obj_est.astimezone(pytz.utc).replace(tzinfo=timezone.utc).timestamp())
            elif header_tag == "Outage":
                impact = Impact("OUTAGE")
            else:
                continue

        table = soup.find("table", "circuitTable")
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) == 9:
                if cols[0].string.strip() == "Name":
                    continue
                data["account"] = cols[0].string.strip()
                data["circuits"].append(CircuitImpact(impact=impact, circuit_id=cols[2].string.strip()))

        return [data]
