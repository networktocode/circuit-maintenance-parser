"""Circuit Maintenance Parser for Equinix Email Notifications."""

import re
from datetime import datetime
from typing import Any, Dict, List

from bs4.element import ResultSet  # type: ignore
from dateutil import parser

from circuit_maintenance_parser.output import Impact
from circuit_maintenance_parser.parser import EmailSubjectParser, Html, Status


class HtmlParserGcx1(Html):
    """Custom Parser for HTML portion of Global Cloud Xchange circuit maintenance notifications."""

    def parse_html(self, soup: ResultSet) -> List[Dict]:
        """Parse an equinix circuit maintenance email.

        Args:
            soup (ResultSet): beautiful soup object containing the html portion of an email.

        Returns:
            Dict: The data dict containing circuit maintenance data.
        """
        data: Dict[str, Any] = {"circuits": []}

        for div in soup.find_all("div"):
            for pstring in div.strings:
                search = re.search("Dear (.*),", pstring)
                if search:
                    data["account"] = search.group(1)

        # Find Circuits
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) == 2 and "Service ID" not in cols[0].text:
                    impact = "NO-IMPACT"
                    if cols[1].text == "At Risk":
                        impact = "REDUCED-REDUNDANCY"

                    data["circuits"].append({"circuit_id": cols[0].text, "impact": impact})

        return [data]

    @staticmethod
    def _isascii(string):
        """Python 3.6 compatible way to determine if string is only english characters.

        Args:
            string (str): string to test if only ascii chars.

        Returns:
            bool: Returns True if string is ascii only, returns false if the string contains extended unicode characters.
        """
        try:
            string.encode("ascii")
            return True
        except UnicodeEncodeError:
            return False

    def _parse_bolded(self, b_elements, data):
        """Parse the <b> / <strong> elements from the notification to capture start and end times, description, and impact.

        Args:
            b_elements (): resulting soup object with all <b> elements
            data (Dict): data from the circuit maintenance

        Returns:
            impact (Status object): impact of the maintenance notification (used in the parse table function to assign an impact for each circuit).
        """
        impact = None
        start_year = 0
        end_year = 0
        for b_elem in b_elements:
            if "SPAN:" in b_elem.text:
                # Formated in DAY MONTH YEAR
                # *SPAN: 02-JUL-2021 - 03-JUL-2021*
                raw_year_span = b_elem.text.strip().split()
                start_year = raw_year_span[1].split("-")[-1]
                end_year = raw_year_span[-1].split("-")[-1]
            if start_year != 0 and "UTC:" in b_elem.text:
                raw_time = b_elem.next_sibling
                # for non english equinix notifications
                # english section is usually at the bottom
                # this skips the non english line at the top
                if not self._isascii(raw_time):
                    continue

                # Expected Format *UTC:* FRIDAY, 02 JUL 10:00 - FRIDAY, 02 JUL 15:00
                # Note this detailed time does not contain the year..
                start_end_time = raw_time.split("-")
                if len(start_end_time) == 2:
                    data["start"] = self.dt2ts(parser.parse(start_end_time[0].strip() + f" {start_year}"))
                    data["end"] = self.dt2ts(parser.parse(start_end_time[1].strip() + f" {end_year}"))
            # all circuits in the notification share the same impact
            if "IMPACT:" in b_elem:
                impact_line = b_elem.next_sibling
                impact_sibling_line = (impact_line.next_sibling and impact_line.next_sibling.text) or ""

                if "No impact to your service" in impact_line:
                    impact = Impact.NO_IMPACT
                elif "There will be service interruptions" in impact_line:
                    impact = Impact.OUTAGE
                elif "There will be service interruptions" in impact_sibling_line:
                    impact = Impact.OUTAGE
                elif "Loss of redundancy" in impact_line:
                    impact = Impact.REDUCED_REDUNDANCY
                elif "Traffic will be re-routed" in impact_line:
                    impact = Impact.REDUCED_REDUNDANCY
        return impact

    def _parse_table(self, theader_elements, data, impact):
        for th_elem in theader_elements:
            if "Account #" in th_elem:
                circuit_table = th_elem.find_parent("table")
                for tr_elem in circuit_table.find_all("tr"):
                    if tr_elem.find(th_elem):
                        continue
                    circuit_info = list(tr_elem.find_all("td"))
                    if circuit_info:
                        if len(circuit_info) == 4:
                            # Equinix Connect notifications contain the IBX name
                            account, _, _, circuit = circuit_info  # pylint: disable=unused-variable
                        elif len(circuit_info) == 14:
                            # Equinix Fabric notifications include a lot of additional detail on seller and subscriber ID's
                            (
                                account,
                                _,
                                _,
                                circuit,
                                _,
                                _,
                                _,
                                _,
                                _,
                                _,
                                _,
                                _,
                                _,
                                _,
                            ) = circuit_info  # pylint: disable=unused-variable
                        elif len(circuit_info) == 3:
                            account, _, circuit = circuit_info  # pylint: disable=unused-variable
                        else:
                            return
                        data["circuits"].append(
                            {
                                "circuit_id": circuit.text,
                                "impact": impact,
                            }
                        )
                        data["account"] = account.text


class SubjectParserGcx1(EmailSubjectParser):
    """Parse the subject of a Global Cloud Xchange circuit maintenance email. The subject contains the maintenance ID and status."""

    def parse_subject(self, subject: str) -> List[Dict]:
        """Parse the Global Cloud Xchange Email subject for summary and status.

        Args:
            subject (str): subject of email
            e.g. 'PE2024020844407 | Emergency | Service Advisory Notice | Span Loss Rectification | 12-Feb-2024 09:00 (GMT) - 12-Feb-2024 17:00 (GMT)'.


        Returns:
            List[Dict]: Returns the data object with summary and status fields.
        """
        data = {}
        search = re.search(
            r"^([A-Z0-9]+) \| (\w+) \| ([\w\s]+) \| ([\w\s]+) \| (\d+-[A-Za-z]{3}-\d{4} \d{2}:\d{2}) \(GMT\) - (\d+-[A-Za-z]{3}-\d{4} \d{2}:\d{2}) \(GMT\)$",
            subject,
        )
        if search:
            data["maintenance_id"] = search.group(1)
            date_format = date_format = "%d-%b-%Y %H:%M"
            data["start"] = self.dt2ts(datetime.strptime(search.group(5), date_format))
            data["end"] = self.dt2ts(datetime.strptime(search.group(6), date_format))
        data["summary"] = search.group(4)
        if "completed" in subject.lower():
            data["status"] = Status.COMPLETED
        elif "rescheduled" in subject.lower():
            data["status"] = Status.RE_SCHEDULED
        elif "scheduled" in subject.lower() or "reminder" in subject.lower() or "notice" in subject.lower():
            data["status"] = Status.CONFIRMED
        elif "cancelled" in subject.lower():
            data["status"] = Status.CANCELLED
        else:
            # Some Global Cloud Xchange notifications don't clearly state a status in their subject.
            # From inspection of examples, it looks like "Confirmed" would be the most appropriate in this case.
            data["status"] = Status.CONFIRMED

        return [data]
