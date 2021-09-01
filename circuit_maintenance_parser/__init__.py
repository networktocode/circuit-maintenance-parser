"""Notifications parser init."""

from typing import Type, Optional, Iterable
from pydantic import BaseModel

from .errors import NonexistentParserError, ParsingError
from .output import Maintenance
from .providers import (
    GenericProvider,
    Cogent,
    EUNetworks,
    GTT,
    Lumen,
    Megaport,
    NTT,
    PacketFabric,
    Telia,
    Telstra,
    Turkcell,
    Verizon,
    Zayo,
)

SUPPORTED_PROVIDERS = (
    GenericProvider,
    Cogent,
    EUNetworks,
    GTT,
    Lumen,
    Megaport,
    NTT,
    PacketFabric,
    Telia,
    Telstra,
    Turkcell,
    Verizon,
    Zayo,
)

SUPPORTED_PROVIDER_NAMES = [provider.get_provider_type() for provider in SUPPORTED_PROVIDERS]
SUPPORTED_ORGANIZER_EMAILS = [provider.get_default_organizer() for provider in SUPPORTED_PROVIDERS]


def init_provider(raw, provider_type=None) -> Optional[GenericProvider]:
    """Returns an instance of the corresponding Notification Parser."""
    try:
        if not provider_type:
            provider_type = GenericProvider.get_provider_type()
        provider_parser_class = get_provider_class(provider_type)
        return provider_parser_class(raw=raw)

    except NonexistentParserError:
        return None


def get_provider_class(provider_name: str) -> Type[GenericProvider]:
    """Returns the Provider parser class for a specific provider_type."""
    provider_name = provider_name.lower()

    for provider_parser in SUPPORTED_PROVIDERS:
        if provider_parser.get_provider_type() == provider_name:
            break
    else:

        raise NonexistentParserError(
            f"{provider_name} is not a currently supported parser. Only {', '.join(SUPPORTED_PROVIDER_NAMES)}"
        )

    return provider_parser


def get_provider_class_from_sender(email_sender: str) -> Type[GenericProvider]:
    """Returns the notification parser class for an email sender address."""

    for provider_parser in SUPPORTED_PROVIDERS:
        if provider_parser.get_default_organizer() == email_sender:
            break
    else:
        raise NonexistentParserError(
            f"{email_sender} is not a currently supported provider parser. Only {', '.join(SUPPORTED_ORGANIZER_EMAILS)}"
        )

    return provider_parser


def get_provider_data_types(provider_name: str) -> Iterable[str]:
    """Returns the expected data types for each provider."""
    provider_name = provider_name.lower()
    for provider in SUPPORTED_PROVIDERS:
        if provider.get_provider_type() == provider_name:
            break
    else:
        raise NonexistentParserError(
            f"{provider_name} is not a currently supported provider. Only {', '.join(SUPPORTED_PROVIDER_NAMES)}"
        )

    return provider.get_data_types()


# TODO: In Release 1.2.0, we introduced new Provider abstraction to accomodate multiple potential parser per provider.
# In order to mantain backwards compatibility until a new major version release (2.x.x) we still mantain the following
# aliases that will be deprecated with the next major version change.


class MaintenanceNotification(BaseModel):
    """Class to keep backwards compatibility after changes in 1.2.0."""

    raw: bytes
    provider_type: str
    sender: str = ""
    subject: str = ""
    source: str = ""

    provider: Optional[GenericProvider] = None

    def process(self) -> Iterable[Maintenance]:
        """Method that returns a list of Maintenance objects."""
        if self.provider:
            return self.provider.process()
        return []


def init_parser(**kwargs) -> Optional[MaintenanceNotification]:
    """Returns an instance of the MaintenanceNotification for backwards compatibility."""
    try:
        provider_type = kwargs.get("provider_type")
        if not provider_type:
            provider_type = GenericProvider.get_provider_type()
        provider_parser_class = get_provider_class(provider_type)
        return_value = MaintenanceNotification(**kwargs)
        return_value.provider = provider_parser_class(raw=kwargs.get("raw"))
        return return_value

    except NonexistentParserError:
        return None


def get_provider_data_type(provider_name: str) -> Optional[str]:
    """Function to return only the first available data_type."""
    for data_type in get_provider_data_types(provider_name):
        return data_type
    return None


# End of backwards compatibility section for Release 1.2.0


__all__ = [
    "init_provider",
    "get_provider_class",
    "get_provider_class_from_sender",
    "get_provider_data_types",
    "ParsingError",
]
