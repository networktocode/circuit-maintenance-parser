"""Circuit Maintenance Parser for Equinix Email Notifications."""
from typing import Any, Dict, List
import re

from bs4.element import ResultSet  # type: ignore
from dateutil import parser

from circuit_maintenance_parser.output import Impact
from circuit_maintenance_parser.parser import Html, EmailSubjectParser, Status


class HtmlParserEquinix(Html):
    """Custom Parser for HTML portion of Equinix circuit maintenance notifications."""

    def parse_html(self, soup: ResultSet) -> List[Dict]:
        """Parse an equinix circuit maintenance email.

        Args:
            soup (ResultSet): beautiful soup object containing the html portion of an email.

        Returns:
            Dict: The data dict containing circuit maintenance data.
        """
        data: Dict[str, Any] = {"circuits": []}

        impact = self._parse_b(soup.find_all("b"), data)
        self._parse_table(soup.find_all("th"), data, impact)
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

    def _parse_b(self, b_elements, data):
        """Parse the <b> elements from the notification to capture start and end times, description, and impact.

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
            if "UTC:" in b_elem:
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
                if "No impact to your service" in impact_line:
                    impact = Impact.NO_IMPACT
                elif "There will be service interruptions" in impact_line.next_sibling.text:
                    impact = Impact.OUTAGE
                elif "Loss of redundancy" in impact_line:
                    impact = Impact.REDUCED_REDUNDANCY
                elif "Traffic will be re-routed" in impact_line:
                    impact = Impact.REDUCED_REDUNDANCY
        return impact

    def _parse_table(self, theader_elements, data, impact):  # pylint: disable=no-self-use
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


class SubjectParserEquinix(EmailSubjectParser):
    """Parse the subject of an equinix circuit maintenance email. The subject contains the maintenance ID and status."""

    def parse_subject(self, subject: str) -> List[Dict]:
        """Parse the Equinix Email subject for summary and status.

        Args:
            subject (str): subject of email
            e.g. 'Scheduled software upgrade in metro connect platform-SG Metro Area Network Maintenance -19-OCT-2021 [5-212760022356]'.


        Returns:
            List[Dict]: Returns the data object with summary and status fields.
        """
        data = {}
        maintenance_id = re.search(r"\[([^[]*)\]$", subject)
        if maintenance_id:
            data["maintenance_id"] = maintenance_id[1]
        data["summary"] = subject.strip().replace("\n", "")
        if "completed" in subject.lower():
            data["status"] = Status.COMPLETED
        elif "rescheduled" in subject.lower():
            data["status"] = Status.RE_SCHEDULED
        elif "scheduled" in subject.lower() or "reminder" in subject.lower():
            data["status"] = Status.CONFIRMED
        else:
            # Some Equinix notifications don't clearly state a status in their subject.
            # From inspection of examples, it looks like "Confirmed" would be the most appropriate in this case.
            data["status"] = Status.CONFIRMED

        return [data]
