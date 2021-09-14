"""AquaComms parser."""
import logging
import re
from datetime import datetime

from circuit_maintenance_parser.parser import EmailSubjectParser, Html, Impact, CircuitImpact, Status

# pylint: disable=too-many-nested-blocks, too-many-branches

logger = logging.getLogger(__name__)


class SubjectParserAquaComms1(EmailSubjectParser):
    """Parser for Seaborn subject string, email type 1."""

    def parse_subject(self, subject):
        """Parse subject of email file.

        Subject: Aqua Comms Planned Outage Work ISSUE=111111 PROJ=999
        """
        data = {}
        search = re.search(r"ISSUE=([0-9]+).PROJ=([0-9]+)", subject)
        if search:
            data["maintenance_id"] = search.group(1)
            data["account"] = search.group(2)
        return [data]


class HtmlParserAquaComms1(Html):
    """Notifications Parser for AquaComms notifications."""

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        self.parse_tables(soup.find_all("table"), data)
        return [data]

    @staticmethod
    def get_tr_value(element):
        """Remove new lines and split key to value."""
        return element.text.replace("\n", "").split(": ")[1].strip()

    def parse_tables(self, tables, data):
        """Parse HTML tables.

        <table>
            <tbody>
                <tr>
                    <td><font>Ticket Number:</font></td>
                    <td><font>11111</font></td>
                </tr>
                <tr>
                    <td><font>Scheduled Start Date & Time:</font></td>
                    <td><font>22:00 12/10/2020 GMT</font></td>
                </tr>
                <tr>
                    <td><font>Scheduled End Date & Time:</font></td>
                    <td><font>22:00 12/10/2020 GMT</font></td>
                </tr>
                ...
            </tbody>
        </table>
        """
        for table in tables:
            for tr_element in table.find_all("tr"):
                if "ticket number" in tr_element.text.lower():
                    data["maintenance_id"] = self.get_tr_value(tr_element)
                elif "update" in tr_element.text.lower():
                    data["summary"] = tr_element.text.replace("\n", "").split(" - ")[1]
                elif "scheduled start date" in tr_element.text.lower():
                    data["start"] = self.dt2ts(datetime.strptime(self.get_tr_value(tr_element), "%H:%M %d/%m/%Y %Z"))
                elif "scheduled end date" in tr_element.text.lower():
                    data["end"] = self.dt2ts(datetime.strptime(self.get_tr_value(tr_element), "%H:%M %d/%m/%Y %Z"))
                elif "service id" in tr_element.text.lower():
                    data["circuits"] = [
                        CircuitImpact(circuit_id=self.get_tr_value(tr_element), impact=Impact("OUTAGE"))
                    ]
        data["status"] = Status.CONFIRMED
