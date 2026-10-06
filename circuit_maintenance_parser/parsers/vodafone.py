"""Vodafone parser."""

import logging
import re
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from bs4.element import ResultSet  # type: ignore
from dateutil import parser

from circuit_maintenance_parser.parser import EmailSubjectParser, Html, Impact, Status

logger = logging.getLogger(__name__)


class HtmlParserVodafone1(Html):
    """Notifications Parser for Vodafone notifications."""

    def parse_html(self, soup: BeautifulSoup) -> List[Dict]:
        """Execute parsing."""
        data: Dict[str, Any] = {"circuits": []}
        self.parse_crq(soup, data)
        self.parse_tables(soup.find_all("table"), data)
        self.parse_bold(soup.find_all("b"), data)

        return [data]

    def parse_tables(self, tables: ResultSet, data: Dict):
        """Parse table element to find circuit ID's and account."""
        for table in tables:
            col_mapping = {}
            for tr_elem in table.find_all("tr"):
                col = 0
                cid = 0
                impact = 0
                # look for table header
                for th_elem in tr_elem.find_all("th"):
                    # Map column headers to column number
                    if th_elem.text.strip() != "":
                        col_mapping[th_elem.text.strip()] = col
                    col += 1

                # look for regular columns
                for td_elem in tr_elem.find_all("td"):
                    if "Customer" in col_mapping and col == col_mapping["Customer"]:
                        data["account"] = td_elem.text.strip()
                    elif "Services Affected" in col_mapping and col == col_mapping["Services Affected"]:
                        cid = td_elem.text.strip()
                    elif "Service Impact" in col_mapping and col == col_mapping["Service Impact"]:
                        # not sure if other impact types exist, can be expanded of need-be. Default to DEGRADED.
                        if "loss of service" in td_elem.text.lower():
                            impact = Impact("OUTAGE")
                        else:
                            impact = Impact("DEGRADED")
                    col += 1

                # at the end of the table row, add circuits to list, if defined
                if cid != 0 and impact != 0:
                    data["circuits"].append({"circuit_id": cid, "impact": impact})

    def parse_bold(self, bolds: ResultSet, data: Dict):
        """Parse B (bold) elements to find summary and start+end date/time.

        Example:
        <b>New Scheduled Start/End Date &amp; Outage Window:</b><br>
        06/04/2026 00:00 to 13/04/2026 00:00 UTC <br>
        """
        window = 0
        for bold in bolds:
            text_lower = bold.text.lower()

            # find start/end date/time
            # in case the window is re-schedulded, the original and new window are listed; ignore original window
            if "original scheduled start" in text_lower:
                continue

            if "scheduled start" in text_lower:
                window_next = bold.next_sibling
                while window_next:
                    text = window_next.text.strip()
                    if text != "":
                        window = text
                        break
                    window_next = window_next.next_sibling

            # find summary
            if "description" in text_lower:
                description_next = bold.next_sibling
                while description_next:
                    text = description_next.text.strip()
                    if text != "":
                        data["summary"] = text
                        break
                    description_next = description_next.next_sibling

        if window != 0:
            start_str, end_str = window.replace(" UTC", "").split(" to ")
            data["start"] = self.dt2ts(parser.parse(start_str, dayfirst=True))
            data["end"] = self.dt2ts(parser.parse(end_str, dayfirst=True))

    def parse_crq(self, soup: ResultSet, data: Dict):
        """Vodafone maintenance_id's are in the format of CRQ[0-9] with 12 digits.

        Please be advised that the Planned Works have been Completed: CRQ000001312927
        """
        text = soup.get_text(separator=" ")
        match = re.search(r"\bCRQ\d{12}\b", text)
        if match:
            data.setdefault("maintenance_id", match.group(0))


class SubjectParserVodafone1(EmailSubjectParser):
    """Parse status and (when present) the CRQ from the subject line."""

    def parse_subject(self, subject: str) -> List[Dict]:
        """Parse the email subject."""
        data: Dict = {}
        subject_lower = subject.lower()

        if "completed" in subject_lower:
            data["status"] = Status("COMPLETED")
        elif "rescheduled" in subject_lower:
            data["status"] = Status("RE-SCHEDULED")
        elif "postponed" in subject_lower or "cancelled" in subject_lower:
            data["status"] = Status("CANCELLED")
        else:
            data["status"] = Status("CONFIRMED")

        crq_match = re.search(r"\bCRQ\d{12}\b", subject)
        if crq_match:
            data["maintenance_id"] = crq_match.group(0)

        return [data]
