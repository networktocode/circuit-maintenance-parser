"""Sparkle parser."""
import logging
from dateutil import parser

from circuit_maintenance_parser.errors import ParserError
from circuit_maintenance_parser.parser import CircuitImpact, Html, Impact, Status

logger = logging.getLogger(__name__)


class HtmlParserSparkle1(Html):
    """Notifications HTML Parser 1 for Sparkle notifications.

    Example:
        <table>
            <tbody>
                <tr>
                    <td><p></p>Maintenance ID</td>
                    <td><p></p>1111 / 2222</td>
                </tr>
                <tr>
                    <td><p></p>Start Date/Time (UTC) Day 1</td>
                    <td><p></p>08/10/2021 03:00 UTC</td>
                </tr>
                <tr>
                    <td><p></p>End Date/Time (UTC) Day 1</td>
                    <td><p></p>08/10/2021 11:00 UTC</td>
                </tr>
                <tr>
                    <td><p></p>Start Date/Time (UTC) Day 2</td>
                    <td><p></p>08/11/2021 03:00 UTC</td>
                </tr>
                <tr>
                    <td><p></p>End Date/Time (UTC) Day 2</td>
                    <td><p></p>08/11/2021 11:00 UTC</td>
                </tr>
                ...
            </tbody>
        </table>
    """

    def parse_html(self, soup):
        """Execute parsing."""
        data = {}
        try:
            return self.parse_tables(soup.find_all("table"), data)
        except Exception as exc:
            raise ParserError from exc

    def clean_string(self, string):
        """Remove hex characters and new lines."""
        return self.remove_hex_characters(string.replace("\n", "")).strip()

    @staticmethod
    def set_all_tickets(tickets, attribute, value):
        """Set the same value for all notifications."""
        for ticket in tickets:
            ticket[attribute] = value

    def parse_tables(self, tables, data_base):
        """Parse HTML tables."""
        data = []
        for table in tables:
            tr_elements = table.find_all("tr")
            for idx, tr_element in enumerate(tr_elements):
                td_elements = tr_element.find_all("td")
                if "sparkle ticket number" in td_elements[0].text.lower():
                    tickets = self.clean_string(td_elements[1].text).split("/ ")
                    for ticket_id in tickets:
                        ticket = data_base.copy()
                        ticket["maintenance_id"] = ticket_id
                        if "start date/time" in tr_elements[idx + 1].text.lower():
                            start = self.clean_string(tr_elements[idx + 1].find_all("td")[1].text)
                            ticket["start"] = self.dt2ts(parser.parse(start))
                        else:
                            raise ParserError("Unable to find start time for ticket " + ticket_id)
                        if "end date/time" in tr_elements[idx + 2].text.lower():
                            end = self.clean_string(tr_elements[idx + 2].find_all("td")[1].text)
                            ticket["end"] = self.dt2ts(parser.parse(end))
                        else:
                            raise ParserError("Unable to find end time for ticket " + ticket_id)
                        idx += 2
                        data.append(ticket)
                elif "circuits involved" in td_elements[0].text.lower():
                    self.set_all_tickets(
                        data,
                        "circuits",
                        [CircuitImpact(impact=Impact.OUTAGE, circuit_id=self.clean_line(td_elements[1].text))],
                    )
                elif "description of work" in td_elements[0].text.lower():
                    self.set_all_tickets(data, "summary", self.clean_string(td_elements[1].text))
        self.set_all_tickets(data, "status", Status.CONFIRMED)
        self.set_all_tickets(data, "account", "Not Available")
        return data
