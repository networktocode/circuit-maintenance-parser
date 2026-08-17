"""KPN parser."""

import logging
from datetime import datetime, timezone
from typing import Dict, List

from circuit_maintenance_parser.errors import ParserError
from circuit_maintenance_parser.output import CircuitImpact, Impact, Status
from circuit_maintenance_parser.parser import Xlsx

logger = logging.getLogger(__name__)

# KPN spreadsheet column names (bilingual Dutch | English headers)
COL_CIRCUIT_ID = "V/G/A-nummer | V/G/A number"
COL_MAINTENANCE_ID = "Astrid/IDA"
COL_START_DATE = "Startdatum | Start date"
COL_START_TIME = "Starttijd | Start time"
COL_END_DATE = "Einddatum | End date"
COL_END_TIME = "Eindtijd | End time"
COL_DOWNTIME = "Onderbrekingsduur | Downtime"
COL_LINE_ID = "Lijnbenaming | Line ID"
COL_STATUS = "Aankondiging"
COL_ACCOUNT = "Bedrijfsnaam A-locatie | Company A-location"

# Dutch status values in the Aankondiging column
_STATUS_MAP = {
    "aankondiging": Status.CONFIRMED,  # announcement
    "wijziging": Status.CONFIRMED,  # change/reschedule — new times supersede old
    "annulering": Status.CANCELLED,  # cancellation
    "afsluiting": Status.COMPLETED,  # closure/completed
}


class XlsxParserKPN1(Xlsx):
    """Parse KPN XLSX maintenance notification spreadsheets."""

    @staticmethod
    def parse_xlsx(records: List[Dict]) -> List[Dict]:
        """Extract maintenance data from KPN Trans_*.xlsx attachment."""
        if not records:
            raise ParserError("Empty KPN spreadsheet.")

        first = records[0]
        _check_required_columns(first)

        maintenance_id = str(first[COL_MAINTENANCE_ID]).strip()
        status = _parse_status(first)
        start = _parse_datetime(first[COL_START_DATE], first[COL_START_TIME])
        end = _parse_datetime(first[COL_END_DATE], first[COL_END_TIME])
        account = str(first.get(COL_ACCOUNT, "")).strip() or "Customer info unavailable"

        circuits = []
        for row in records:
            circuit_id = str(row[COL_CIRCUIT_ID]).strip()
            if not circuit_id:
                continue
            impact = _parse_impact(row)
            circuits.append(CircuitImpact(circuit_id=circuit_id, impact=impact))

        line_id = str(first.get(COL_LINE_ID, "")).strip()
        summary = f"KPN maintenance {maintenance_id}" + (f" ({line_id})" if line_id else "")

        return [
            {
                "maintenance_id": maintenance_id,
                "status": status,
                "start": int(start.timestamp()),
                "end": int(end.timestamp()),
                "circuits": circuits,
                "summary": summary,
                "account": account,
            }
        ]


def _check_required_columns(row: Dict) -> None:
    required = [COL_CIRCUIT_ID, COL_MAINTENANCE_ID, COL_START_DATE, COL_START_TIME, COL_END_DATE, COL_END_TIME]
    missing = [c for c in required if c not in row]
    if missing:
        raise ParserError(f"KPN spreadsheet missing required columns: {missing}")


def _parse_datetime(date_str: str, time_str: str) -> datetime:
    """Combine KPN date (DD-MM-YYYY) and time (HH:MM) into a UTC-aware datetime."""
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%d-%m-%Y %H:%M")
        return dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError) as exc:
        raise ParserError(f"KPN could not parse date/time '{date_str} {time_str}': {exc}") from exc


def _parse_status(row: Dict) -> Status:
    """Map the Dutch status column value to a Status enum."""
    raw = str(row.get(COL_STATUS, "")).strip().lower()
    status = _STATUS_MAP.get(raw)
    if status is None:
        logger.warning("Unrecognized KPN status %r, defaulting to CONFIRMED.", raw)
        return Status.CONFIRMED
    return status


def _parse_impact(row: Dict) -> Impact:
    """Derive impact from the downtime-minutes column.

    KPN's 'Onderbrekingsduur | Downtime' field is an integer number of minutes.
    Zero minutes means no service disruption; any positive value is an outage.
    """
    raw = row.get(COL_DOWNTIME)
    try:
        minutes = int(raw)
    except (TypeError, ValueError):
        logger.warning("KPN could not parse downtime %r, defaulting to OUTAGE.", raw)
        return Impact.OUTAGE
    if minutes == 0:
        return Impact.NO_IMPACT
    return Impact.OUTAGE
