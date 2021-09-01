"""Definition of Data classes."""
from typing import List, NamedTuple

import email
from pydantic import BaseModel, Extra


class DataPart(NamedTuple):
    """Simplest data unit to be parsed."""

    type: str
    content: bytes


class NotificationData(BaseModel, extra=Extra.forbid):
    """Base class for Notification Data types."""

    data_parts: List[DataPart] = []

    @classmethod
    def init(cls, data_type: str, data_content: bytes):
        """Initialize the data_parts with only one DataPart object."""
        return cls(data_parts=[DataPart(data_type, data_content)])

    @classmethod
    def init_from_email_bytes(cls, raw_email_bytes: bytes):
        """Initialize the data_parts from an email defined as raw bytes.."""
        raw_email_string = raw_email_bytes.decode("utf-8")
        email_message = email.message_from_string(raw_email_string)
        return cls.init_from_emailmessage(email_message)

    @classmethod
    def init_from_emailmessage(cls, email_message):
        """Initialize the data_parts from an email.message.Email object."""
        data_parts = []
        for part in email_message.walk():
            data_parts.append(DataPart(part.get_content_type(), part.get_payload()))

        # Adding extra headers that are interesting to be parsed
        data_parts.append(DataPart("email-header-subject", email_message["Subject"]))
        # TODO: Date could be used to extend the "Stamp" time of a notification when not available, but we need a parser
        data_parts.append(DataPart("email-header-date", email_message["Date"]))

        return cls(data_parts=data_parts)
