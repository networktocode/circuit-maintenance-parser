"""Notification Parser exceptions."""


class ParsingError(Exception):
    """Unable to successfully parse the notification."""

    def __init__(
        self, *args, related_exceptions=None, **kwargs,
    ):
        """Extend init to add related_exceptions coming from multiple related errors."""
        super().__init__(*args, **kwargs)
        self.related_exceptions = related_exceptions or []


class MissingMandatoryFields(Exception):
    """Missing one or more mandatory fields."""


class NonexistentParserError(Exception):
    """Nonexistent Notification Parser."""
