"""Netflix parser."""
import hashlib
import logging
import re

from dateutil import parser

from circuit_maintenance_parser.parser import CircuitImpact, Impact, Status, Text

# pylint: disable=too-many-nested-blocks, too-many-branches

logger = logging.getLogger(__name__)


class TextParserNetflix1(Text):
    """Parse text body of Netflix AS2906 (not 40027) email."""

    def parse_text(self, text):
        """Parse text.

        Example:
            Example.com (AS65001),

                Netflix (AS2906) will be performing scheduled maintenance in Edgeconnex LAS01,
                at 2024-01-31 18:00:00+00:00 UTC.

                Traffic will drain away onto redundant equipment prior to the start of the
                maintenance.

                After approximately 1 hour of draining, you will see BGP sessions and associated
                interfaces flap.

                Expected downtime will be approximately 60 minutes.  Traffic will be restored
                shortly thereafter.

                Please do not shut down any links or BGP sessions during this downtime.

                Your IPs:
                192.0.2.1
                2001:db8::1
        """
        data = {"circuits": []}
        impact = Impact.OUTAGE
        status = Status.CONFIRMED
        minutes = 0
        hours = 0
        maintenance_id = ""

        for line in text.splitlines():
            search = re.search(r" \((AS[0-9]+)\),$", line)
            if search:
                data["account"] = search.group(1)
            if " maintenance in " in line:
                data["summary"] = line.lstrip()
                search = re.search(r" ([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})\+00:00 UTC", line)
                if search:
                    data["start"] = self.dt2ts(parser.parse(search.group(1)))
            search = re.search(r" ([0-9]+) minutes", line)
            if search:
                minutes = int(search.group(1))
            search = re.search(r" ([0-9]+) hours", line)
            if search:
                hours = int(search.group(1))
            if re.search(r"^[.0-9]+$", line.lstrip()):
                data["circuits"].append(CircuitImpact(circuit_id=line.lstrip(), impact=impact))
                maintenance_id += line + "/"
            if re.search(r"^[0-9a-f:]+$", line.lstrip()):
                data["circuits"].append(CircuitImpact(circuit_id=line.lstrip(), impact=impact))
                maintenance_id += line + "/"

        data["end"] = data["start"] + hours * 3660 + minutes * 60

        # Netflix does not send a maintenance ID, so a hash value is being generated using the start,
        #  end and IDs of all circuits in the notification.
        maintenance_id += str(data["start"]) + "/" + str(data["end"])
        data["maintenance_id"] = hashlib.md5(maintenance_id.encode("utf-8")).hexdigest()  # nosec
        data["status"] = status
        return [data]
