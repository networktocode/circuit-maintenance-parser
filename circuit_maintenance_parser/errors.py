"""Notification Parser exceptions."""


class ProviderError(Exception):
    """Unable to successfully parse the notification."""

    def __init__(
        self, *args, related_exceptions=None, **kwargs,
    ):
        """Extend init to add related_exceptions coming from multiple related errors."""
        super().__init__(*args, **kwargs)
        self.related_exceptions = related_exceptions or []


class ProcessorError(Exception):
    """Nonexistent Notification Provider."""


class ParsingError(Exception):
    """Nonexistent Notification Provider."""


class MissingMandatoryFields(Exception):
    """Missing one or more mandatory fields."""


class NonexistentParserError(Exception):
    """Nonexistent Notification Parser."""


class NonexistentProviderError(Exception):
    """Nonexistent Notification Provider."""
