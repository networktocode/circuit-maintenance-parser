"""Google parser."""
import logging
import re
from datetime import datetime

from circuit_maintenance_parser.parser import Html, Impact, CircuitImpact, Status

# pylint: disable=too-many-nested-blocks, too-many-branches

logger = logging.getLogger(__name__)


class HtmlParserGoogle1(Html):
    """Notifications Parser for Google notifications."""

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        data["circuits"] = []
        data["status"] = Status.CONFIRMED

        for span in soup.find_all("span"):
            if span.string is None:
                continue
            if span.string.strip() == "Start Time:":
                dt_str = span.next_sibling.string.strip()
                data["start"] = self.dt2ts(datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S %z UTC"))
            elif span.string.strip() == "End Time:":
                dt_str = span.next_sibling.string.strip()
                data["end"] = self.dt2ts(datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S %z UTC"))
            elif span.string.strip() == "Peer ASN:":
                data["account"] = span.parent.next_sibling.string.strip()
            elif span.string.strip() == "Google Neighbor Address(es):":
                googleaddr = span.parent.next_sibling.string.strip()
            elif span.string.strip() == "Peer Neighbor Address(es):":
                cid = googleaddr + "-" + span.parent.next_sibling.string.strip()
                data["circuits"].append(CircuitImpact(circuit_id=cid, impact=Impact.OUTAGE))

        summary = list(soup.find("div").find("div").strings)[-1].strip()
        match = re.search(r" - Reference (.*)$", summary)
        data["summary"] = summary
        data["maintenance_id"] = match[1]

        return [data]
