"""Definition of Data classes."""
import logging

from collections import namedtuple
from typing import List

import email
from pydantic import BaseModel, Extra


logger = logging.getLogger(__name__)


DataPart = namedtuple("DataPart", "type content")


class NotificationData(BaseModel, extra=Extra.forbid):
    """Base class for Notification Data types."""

    _data_parts: List[DataPart] = []

    def get_data_parts(self) -> List[DataPart]:
        """Return an Iterable of Data objects from each NotificationData class."""
        return self._data_parts

    def init(self, data_type, data_content):
        """Simple init of one part notification."""
        self._data_parts.append(DataPart(data_type, data_content))
        return self

    def init_from_email_bytes(self, raw_email_bytes: bytes):
        """Initialize the data_parts from an email format"""
        raw_email_string = raw_email_bytes.decode("utf-8")
        email_message = email.message_from_string(raw_email_string)
        return self.init_from_emailmessage(email_message)

    def init_from_emailmessage(self, email_message):
        """Initialize the data_parts from an email format"""
        for part in email_message.walk():
            self._data_parts.append(DataPart(part.get_content_type(), part.get_payload()))

        # Adding extra headers that are interesting to be parsed
        self._data_parts.append(DataPart("email-header-subject", email_message["Subject"]))
        # TODO: Date could be used to extend the "Stamp" time of a notification when not available, but we need a parser
        self._data_parts.append(DataPart("email-header-date", email_message["Date"]))

        return self
