"""Crown Castle Fiber parser."""
import logging
import re
from datetime import datetime

from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status

# pylint: disable=too-many-nested-blocks, too-many-branches

logger = logging.getLogger(__name__)


class HtmlParserCrownCastle1(Html):
    """Notifications Parser for Crown Castle Fiber notifications."""

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        data["circuits"] = []

        data["status"] = self.get_status(soup)

        for p in soup.find_all("p"):
            for s in p.strings:
                search = re.match(r"^Dear (.*),", s)
                if search:
                    data["account"] = search.group(1)

        self.parse_strong(soup, data)

        table = soup.find("table", "timezonegrid")
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) == 5:
                if cols[4].string.strip() == "GMT":
                    st_dt = cols[0].string.strip() + " " + cols[1].string.strip() + " GMT"
                    en_dt = cols[2].string.strip() + " " + cols[3].string.strip() + " GMT"
                    data["start"] = self.dt2ts(datetime.strptime(st_dt, "%m/%d/%Y %I:%M %p %Z"))
                    data["end"] = self.dt2ts(datetime.strptime(en_dt, "%m/%d/%Y %I:%M %p %Z"))

        table = soup.find("table", id="circuitgrid")
        if table is not None:
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) == 6:
                    if cols[4].string.strip() == "None":
                        impact = Impact("NO-IMPACT")
                    else:
                        impact = Impact("OUTAGE")
                    data["circuits"].append(CircuitImpact(impact=impact, circuit_id=cols[0].string.strip()))

        return [data]

    def parse_strong(self, soup, data):
        """Parse the strong tags, to find summary and maintenance ID info."""
        for strong in soup.find_all("strong"):
            if strong.string.strip() == "Ticket Number:":
                data["maintenance_id"] = strong.next_sibling.strip()
            if strong.string.strip() == "Description:":
                summary = strong.parent.next_sibling.next_sibling.contents[0].string.strip()
                summary = re.sub(r"[\n\r]", "", summary)
                data["summary"] = summary
            if strong.string.strip().startswith("Work Description:"):
                for sibling in strong.parent.next_siblings:
                    summary = "".join(sibling.strings)
                    summary = re.sub(r"[\n\r]", "", summary)
                    if summary != "":
                        data["summary"] = summary
                        break

    def get_status(self, soup):
        """Get the status of the maintenance."""
        for p in soup.find_all("p"):
            for s in p.strings:
                if "has been completed." in s:
                    return Status("COMPLETED")

        for u in soup.find_all("u"):
            if u.string is None:
                continue
            if u.string.strip() == "Maintenance Notification":
                return Status("CONFIRMED")
            if u.string.strip() == "Emergency Notification":
                return Status("CONFIRMED")
            if u.string.strip() == "Maintenance Notification - Rescheduled Event":
                return Status("RE-SCHEDULED")
            if u.string.strip() == "Maintenance Cancellation Notification":
                return Status("CANCELLED")

            return Status("NO-CHANGE")
