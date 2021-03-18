"""Notifications parser init."""

from typing import Type

from .errors import NonexistentParserError
from .parser import MaintenanceNotification, ICal
from .parsers.eunetworks import ParserEUNetworks
from .parsers.ntt import ParserNTT
from .parsers.packetfabric import ParserPacketFabric
from .parsers.zayo import ParserZayo


SUPPORTED_PROVIDER_PARSERS = (
    ParserEUNetworks,
    ParserNTT,
    ParserPacketFabric,
    ParserZayo,
    ICal,
)

SUPPORTED_PROVIDER_NAMES = [parser.get_default_provider() for parser in SUPPORTED_PROVIDER_PARSERS]
SUPPORTED_ORGANIZER_EMAILS = [parser.get_default_organizer() for parser in SUPPORTED_PROVIDER_PARSERS]


def get_parser(provider_name: str) -> Type[MaintenanceNotification]:
    """Returns the notification parser class for a specific provider."""
    provider_name = provider_name.lower()

    for parser in SUPPORTED_PROVIDER_PARSERS:
        if parser.get_default_provider() == provider_name:
            break
    else:

        raise NonexistentParserError(
            f"{provider_name} is not a currently supported parser. Only {', '.join(SUPPORTED_PROVIDER_NAMES)}"
        )

    return parser


def get_parser_from_sender(email_sender: str) -> Type[MaintenanceNotification]:
    """Returns the notification parser class for an email sender address."""

    for parser in SUPPORTED_PROVIDER_PARSERS:
        if parser.get_default_organizer() == email_sender:
            break
    else:
        raise NonexistentParserError(
            f"{email_sender} is not a currently supported parser. Only {', '.join(SUPPORTED_ORGANIZER_EMAILS)}"
        )

    return parser


def get_provider_data_type(provider_name: str) -> str:
    """Returns the expected data type for each provider."""
    provider_name = provider_name.lower()

    for parser in SUPPORTED_PROVIDER_PARSERS:
        if parser.get_default_provider() == provider_name:
            break
    else:
        raise NonexistentParserError(
            f"{provider_name} is not a currently supported parser. Only {', '.join(SUPPORTED_PROVIDER_NAMES)}"
        )

    return parser.get_data_type()


__all__ = ["get_parser", "get_parser_from_sender", "get_provider_data_type"]
