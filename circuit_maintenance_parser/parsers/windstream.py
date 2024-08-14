"""Windstream parser."""
import logging
from datetime import timezone

from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status
from circuit_maintenance_parser.utils import convert_timezone

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

        impact = soup.find("td", string="Outage").find_next_sibling("td").string
        if impact:
            impact = Impact("OUTAGE")

        maint_id = soup.find("td", string="WMT:").find_next_sibling("td").string
        if maint_id:
            data["maintenance_id"] = maint_id

        event = soup.find("td", string="Event Start Date & Time:").find_next_sibling("td").string
        if event:
            dt_time = convert_timezone(event)
            data["start"] = int(dt_time.replace(tzinfo=timezone.utc).timestamp())
            event = ""

        event = soup.find("td", string="Event End Date & Time:").find_next_sibling("td").string
        if event:
            dt_time = convert_timezone(event)
            data["end"] = int(dt_time.replace(tzinfo=timezone.utc).timestamp())
            event = ""

        table = soup.find("table", "circuitTable")
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) == 9:
                if cols[0].string.strip() == "Name":
                    continue
                data["account"] = cols[0].string.strip()
                data["circuits"].append(CircuitImpact(impact=impact, circuit_id=cols[2].string.strip()))

        return [data]
