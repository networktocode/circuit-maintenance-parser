"""ATT Parser."""

import logging
import re
import string
from typing import Dict, List

import dateutil
from bs4.element import ResultSet  # type: ignore
from circuit_maintenance_parser.parser import CircuitImpact, Html, Impact, Status, Xlsx


logger = logging.getLogger(__name__)

RE_EVENT = re.compile(
    r"Event ID: (.*)[ \n]"
    r"Customer Impact Description: (.*)[ \n]"
    r"Summary: (.*)[ \n]"
    r"Description: (.*)[ \n]"
    r"Business Risk: (.*)[ \n]"
)
RE_MAINTENANCE_WINDOW_GMT = re.compile(r"Start Time: (.* GMT).*End Time: (.* GMT)")
RE_MAINTENANCE_WINDOW_NO_TIMEZONE = re.compile(r"Start Time: (.*)[ \n]End Time: (.*)")


class XlsxParserATT1(Xlsx):
    """Xlsx Parser for ATT file attachments."""

    @staticmethod
    def parse_xlsx(records: List[Dict]) -> List[Dict]:
        """Parses ATT xlsx attachments."""
        impact = Impact.OUTAGE
        account_name, circuit_id_key = get_account_and_circuit_id_key(records[0])
        circuit_ids = [r[circuit_id_key] for r in records]
        if "Customer" in records[0]:
            circuit_ids = [normalize_lec_circuit_id(cid) for cid in circuit_ids]
        circuits = [CircuitImpact(impact=impact, circuit_id=cid) for cid in circuit_ids]
        data = [
            {
                "account": account_name,
                "circuits": circuits,
            }
        ]
        return data


class HtmlParserATT1(Html):
    """Notifications Parser for ATT notifications."""

    def parse_html(self, soup):
        """Parse ATT HTML notification."""
        logger.debug("Parsing ATT HTML notification.")
        data = self.parse_p_tags(soup)
        data["start"] = self.dt2ts(data["start"])
        data["end"] = self.dt2ts(data["end"])
        data["status"] = Status.CONFIRMED
        return [data]

    @staticmethod
    def parse_p_tags(soup: ResultSet) -> Dict:
        """Parse <p> tags in HTML."""
        data = {}
        p_tags = soup.find_all("p")

        for tag in p_tags:
            text = tag.text.strip()
            text = remove_unprintable(text)

            if match := RE_EVENT.search(text):
                event_id, impact, summary, description, _ = match.groups()
                data["maintenance_id"] = event_id
                data["summary"] = f"{summary}: {impact} {description}"

            elif match := RE_MAINTENANCE_WINDOW_GMT.search(text):
                start_time_text, end_time_text = match.groups()
                data["start"] = dateutil.parser.parse(start_time_text)
                data["end"] = dateutil.parser.parse(end_time_text)

            elif match := RE_MAINTENANCE_WINDOW_NO_TIMEZONE.search(text):
                start_time_text, end_time_text = match.groups()
                data["start"] = dateutil.parser.parse(start_time_text)
                data["end"] = dateutil.parser.parse(end_time_text)

        return data


def get_account_and_circuit_id_key(record: Dict) -> tuple[str, str]:
    """Return the account name and the key used to retrieve circuits IDs.

    The key names may vary depending on the ATT business unit that initiated the notice.
    """
    if account := record.get("Customer"):
        circuit_id_key = "Circuit/Asset"
    elif account := record.get("Customer Name"):
        circuit_id_key = "Circuit ID"
    elif account := record.get("Customer Names"):
        circuit_id_key = "Customer Circuit ID"
    else:
        account = circuit_id_key = ""

    return str(account), circuit_id_key


def normalize_lec_circuit_id(circuit_id: str) -> str:
    """Standardize circuit IDs."""
    circuit_id, *_ = circuit_id.split()
    circuit_id = re.sub(r"^0+", "", circuit_id)  # Remove leading zeros.
    circuit_id = re.sub(r"0+$", "ATI", circuit_id)  # Remove trailing zeros.
    return circuit_id


def remove_unprintable(text: str) -> str:
    """Remove non-printing characters from text."""
    return "".join(c for c in text if c in string.printable)
