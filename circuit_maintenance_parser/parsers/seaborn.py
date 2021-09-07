"""Seaborn parser."""
import logging
import re

from dateutil import parser

from circuit_maintenance_parser.parser import CircuitImpact, Html, Impact, Status, EmailSubjectParser

# pylint: disable=too-many-branches


logger = logging.getLogger(__name__)


class SubjectParserSeaborn1(EmailSubjectParser):
    """Parser for Seaborn subject string, email type 1.

    Subject: [{ACOUNT NAME}] {MAINTENACE ID} {DATE}
             [Customer Direct] 1111 08/14
    """

    def parse_subject(self, subject):
        """Parse subject of email file."""
        data = {}
        search = re.search(r".+\[(.+)\].([0-9]+).+", subject)
        if search:
            data["account"] = search.group(1)
            data["maintenance_id"] = search.group(2)
        return [data]


class SubjectParserSeaborn2(EmailSubjectParser):
    """Parser for Seaborn subject string, email type 2.

    Subject: [## {ACCOUNT NUMBER} ##] Emergency Maintenance Notification CID: {CIRCUIT} TT#{MAINTENACE ID}
             [## 11111 ##] Emergency Maintenance Notification CID: AAA-AAAAA-AAAAA-AAA1-1111-11 TT#1111
    """

    def parse_subject(self, subject):
        """Parse subject of email file."""
        data = {}
        search = re.search(r".+\[## ([0-9]+) ##\].+", subject)
        if search:
            data["account"] = search.group(1)
        return [data]


class HtmlParserSeaborn1(Html):
    """Notifications HTML Parser 1 for Seaborn notifications.

    <div>
        <p>DESCRIPTION: This is a maintenance notification.</p>
        <p>SERVICE IMPACT: 05 MINUTE OUTAGE</p>
        <p>LOCATION: London</p>
        ...
    </div>
    """

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        self.parse_body(soup, data)
        return [data]

    def parse_body(self, body, data):
        """Parse HTML body."""
        data["circuits"] = []
        p_elements = body.find_all("p")

        for index, element in enumerate(p_elements):
            if "DESCRIPTION" in element.text:
                data["summary"] = element.text.split(":")[1].strip()
            elif "SCHEDULE" in element.text:
                schedule = p_elements[index + 1].text
                start, end = schedule.split(" - ")
                data["start"] = self.dt2ts(parser.parse(start))
                data["end"] = self.dt2ts(parser.parse(end))
                data["status"] = Status("CONFIRMED")
            elif "AFFECTED CIRCUIT" in element.text:
                circuit_id = element.text.split(": ")[1]
                data["circuits"].append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=circuit_id))


class HtmlParserSeaborn2(Html):
    """Notifications  HTML Parser 2 for Seaborn notifications.

    <div>
        <div>DESCRIPTION: This is a maintenance notification.</div>
        <div>SERVICE IMPACT: 05 MINUTE OUTAGE</div>
        <div>LOCATION: London</div>
        ...
    </div>
    """

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        self.parse_body(soup, data)
        return [data]

    def parse_body(self, body, data):
        """Parse HTML body."""
        data["circuits"] = []
        div_elements = body.find_all("div")
        for element in div_elements:
            if "Be advised" in element.text:
                if "been rescheduled" in element.text:
                    data["status"] = Status["RE_SCHEDULED"]
                elif "been scheduled" in element.text:
                    data["status"] = Status["CONFIRMED"]
            elif "Description" in element.text:
                data["summary"] = element.text.split(":")[1].strip()
            elif "Seaborn Ticket" in element.text:
                data["maintenance_id"] = element.text.split(":")[1]
            elif "Start date" in element.text:
                start = element.text.split(": ")[1]
                data["start"] = self.dt2ts(parser.parse(start))
            elif "Finish date" in element.text:
                end = element.text.split(": ")[1]
                data["end"] = self.dt2ts(parser.parse(end))
            elif "Circuit impacted" in element.text:
                circuit_id = self.remove_hex_characters(element.text).split(":")[1]
                data["circuits"].append(CircuitImpact(impact=Impact("OUTAGE"), circuit_id=circuit_id))
