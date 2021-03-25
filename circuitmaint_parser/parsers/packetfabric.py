"""PacketFabric parser."""
from ..parser import ICal


class ParserPacketFabric(ICal):
    """PacketFabric Parser class."""

    # Default values for PacketFabric notifications
    _default_provider = "packetfabric"
    _default_organizer = "support@packetfabric.com"
