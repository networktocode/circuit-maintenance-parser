"""GTT parser."""
import logging
import re

from dateutil import parser

from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status

# pylint: disable=too-many-branches


logger = logging.getLogger(__name__)


class HtmlParserGTT1(Html):
    """Notifications Parser for GTT notifications."""

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        self.parse_tables(soup.find_all("table"), data)
        return [data]

    def parse_tables(self, tables, data):
        """Parse HTML tables."""
        for table in tables:
            for td_element in table.find_all("td"):
                if "Planned Work Notification" in td_element.text:
                    # Match example: `Planned Work Notification: 6048019 - Cancelled`
                    # Group 1 matches the maintenance ID
                    # Group 2 matches the status of the notification
                    groups = re.search(r".+: ([0-9]+) - ([A-Z][a-z]+)", td_element.text.strip())
                    if groups:
                        data["maintenance_id"] = groups.groups()[0]
                        status = groups.groups()[1]
                        if status == "Reminder":
                            data["status"] = Status["CONFIRMED"]
                        elif status == "Update":
                            data["status"] = Status["RE_SCHEDULED"]
                        elif status == "Cancelled":
                            data["status"] = Status["CANCELLED"]
                            # When a email is cancelled there is no start or end time specificed
                            # Setting this to 0 and 1 stops any errors from pydantic
                            data["start"] = 0
                            data["end"] = 1
                elif "Start" in td_element.text:
                    start = parser.parse(td_element.next_sibling.next_sibling.text)
                    data["start"] = self.dt2ts(start)
                elif "End" in td_element.text:
                    end = parser.parse(td_element.next_sibling.next_sibling.text)
                    data["end"] = self.dt2ts(end)
            num_columns = len(table.find_all("th"))
            if num_columns:
                data["circuits"] = []
                for row in table.find_all("tr")[1:]:
                    cells = row.find_all("td")
                    data["circuits"].append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=cells[1].text.strip()))
                    data["account"] = cells[2].text.strip()
