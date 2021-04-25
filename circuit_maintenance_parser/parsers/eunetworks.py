"""PacketFabric parser."""
from ..parser import ICal


class ParserEUNetworks(ICal):
    """EUNetworks Parser class."""

    # Default values for EuNetworks notifications
    _default_provider = "eunetworks"
    _default_organizer = "noc@eunetworks.com"
