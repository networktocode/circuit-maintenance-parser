"""NTT parser."""
from ..parser import ICal


class ParserNTT(ICal):
    """NTT Parser class."""

    provider_type: str = "ntt"

    # Default values for NTT notifications
    _default_provider = "ntt"
    _default_organizer = "noc@us.ntt.net"
