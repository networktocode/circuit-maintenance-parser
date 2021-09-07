"""HGC parser."""
import logging
import re

from dateutil import parser

from circuit_maintenance_parser.parser import EmailSubjectParser, Html, Impact, CircuitImpact, Status

# pylint: disable=too-many-branches


logger = logging.getLogger(__name__)


class SubjectParserHGC1(EmailSubjectParser):
    """HGC subject parser."""

    def parse_subject(self, subject):
        """Parse HGC subject string.

        Examples:
            HGC Maintenance Work Notification - Network to Code _ CIR0000001 (TIC00000000000001)
            HGC Maintenance Work Notification - Network to Code | CIR0000001 | TIC00000000000001
        """
        data = {}
        search = re.search(r"^.+\((.+)\)", subject.replace("\n", ""))
        if search:
            data["maintenance_id"] = search.group(1)
        else:
            split = subject.split(" | ")
            data["maintenance_id"] = split[2]
        return [data]


class HtmlParserHGC1(Html):
    """HGC HTML 1 parser."""

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        self.parse_table(soup.find_all("table"), data)
        data["status"] = Status.CONFIRMED
        return [data]

    def parse_table(self, tables, data):
        """Parse HTML tables.

        <table>
            <tr>
                <td><p>Circuit ID</p></td>
                <td><p>:</p></td>
                <td><p>CIR00000001</p></td>
            </tr>
            <tr>
                <td><p>Customer</p></td>
                <td><p>:</p></td>
                <td><p>Network to Code</p></td>
            </tr>
            ...
        </table>
        """
        circuit_id = None
        for table in tables:
            td_elements = table.find_all("td")
            for idx, td_element in enumerate(td_elements):
                if "circuit id" in td_element.text.lower():
                    circuit_id = td_elements[idx + 2].text.strip()
                elif "customer" in td_element.text.lower():
                    data["account"] = td_elements[idx + 2].text.strip()
                elif "maintenance window start date" in td_element.text.lower():
                    data["start"] = self.dt2ts(parser.parse(td_elements[idx + 2].text.strip()))
                elif "maintenance window end date" in td_element.text.lower():
                    data["end"] = self.dt2ts(parser.parse(td_elements[idx + 2].text.strip()))
                elif "description" in td_element.text.lower():
                    data["summary"] = td_elements[idx + 2].text.strip()
                elif "service impact" in td_element.text.lower():
                    if "down throughout maintenance window" in td_elements[idx + 2].text:
                        impact = Impact("OUTAGE")
                    else:
                        impact = Impact("OUTAGE")
                    data["circuits"] = [CircuitImpact(impact=impact, circuit_id=circuit_id)]


class HtmlParserHGC2(Html):
    """HGC HTML 2 parser."""

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        self.parse_body(soup.find_all("span"), data)
        data["status"] = Status.CONFIRMED
        return [data]

    def parse_body(self, span_elements, data):
        """Parse HTML body.

        <div>
            <span>Circuit ID:<wbr>CIR000001</span>
            <span>Customer:<wbr>Network to Code</span>
            ...
        </div>
        """
        circuit_id = None
        for span_element in span_elements:
            if "circuit id:" in span_element.text.lower():
                circuit_id = span_element.text.split(":")[1].strip()
            elif "customer:" in span_element.text.lower():
                data["account"] = span_element.text.split(":")[1].strip()
            elif "maintenance window start date" in span_element.text.lower():
                data["start"] = self.dt2ts(parser.parse(span_element.text.split(":")[1].strip()))
            elif "maintenance window end date" in span_element.text.lower():
                data["end"] = self.dt2ts(parser.parse(span_element.text.split(":")[1].strip()))
            elif "description:" in span_element.text.lower():
                data["summary"] = span_element.text.split(":")[1].strip()
            elif "service impact:" in span_element.text.lower():
                if "down throughout maintenance window" in span_element.text.split(":")[1]:
                    impact = Impact("OUTAGE")
                else:
                    impact = Impact("OUTAGE")
                data["circuits"] = [CircuitImpact(impact=impact, circuit_id=circuit_id)]
