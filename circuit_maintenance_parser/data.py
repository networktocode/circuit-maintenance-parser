"""Definition of Data classes."""
from typing import List, NamedTuple

import email
from pydantic import BaseModel, Extra


class DataPart(NamedTuple):
    """Simplest data unit to be parsed."""

    # type is an arbitrary string that is used to match the DataPart to the Parser class, that contains _data_types
    type: str
    content: bytes


class NotificationData(BaseModel, extra=Extra.forbid):
    """Base class for Notification Data types."""

    data_parts: List[DataPart] = []

    def add_data_part(self, data_type: str, data_content: bytes):
        """Add a DataPart element into the instance data_parts."""
        self.data_parts.append(DataPart(data_type, data_content))

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
    def walk_email(cls, email_message, data_parts):
        """Recursive walk_email using Set to not duplicate data entries."""
        for part in email_message.walk():
            if "image" in part.get_content_type():
                # Not interested in parsing images/QRs yet
                continue

            if "multipart" in part.get_content_type():
                for inner_part in part.get_payload():
                    if isinstance(inner_part, email.message.Message):
                        cls.walk_email(inner_part, data_parts)
            elif "message/rfc822" in part.get_content_type():
                if isinstance(part.get_payload(), email.message.Message):
                    cls.walk_email(part.get_payload(), data_parts)
            else:
                data_parts.add(DataPart(part.get_content_type(), part.get_payload(decode=True)))

    @classmethod
    def init_from_emailmessage(cls, email_message):
        """Initialize the data_parts from an email.message.Email object."""
        data_parts = set()
        cls.walk_email(email_message, data_parts)

        # Adding extra headers that are interesting to be parsed
        data_parts.add(DataPart("email-header-subject", email_message["Subject"].encode()))
        # TODO: Date could be used to extend the "Stamp" time of a notification when not available, but we need a parser
        data_parts.add(DataPart("email-header-date", email_message["Date"].encode()))
        return cls(data_parts=list(data_parts))
