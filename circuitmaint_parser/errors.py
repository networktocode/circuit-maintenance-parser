"""Notification Parser exceptions."""


class ParsingError(Exception):
    """Unable to successfully parse the notification."""


class MissingMandatoryFields(Exception):
    """Missing one or more mandatory fields."""


class NonexistentParserError(Exception):
    """Nonexistent Notification Parser."""
