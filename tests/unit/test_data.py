"""Tests NotificationData."""

import email
import os
from pathlib import Path

from circuit_maintenance_parser.data import NotificationData

dir_path = os.path.dirname(os.path.realpath(__file__))


def test_init_from_raw():
    """Test the init_data_raw function."""
    data = NotificationData.init_from_raw("my_type", b"my_content")
    assert isinstance(data, NotificationData)
    assert len(data.data_parts) == 1
    assert data.data_parts[0].type == "my_type"
    assert data.data_parts[0].content == b"my_content"


def test_init_from_raw_with_issue():
    """Test the init_data_raw function with issue."""
    data = NotificationData.init_from_raw({}, {})
    assert data is None


def test_init_from_email_bytes():
    """Test the email data load."""
    with open(Path(dir_path, "data", "email", "test_sample_message.eml"), "rb") as email_file:
        email_raw_data = email_file.read()
    data = NotificationData.init_from_email_bytes(email_raw_data)
    assert isinstance(data, NotificationData)
    assert len(data.data_parts) == 5


def test_init_from_email_with_issue():
    """Test the init_data_email function with issue."""
    data = NotificationData.init_from_email_bytes("")
    assert data is None


def test_init_from_emailmessage():
    """Test the emailmessage data load."""
    with open(Path(dir_path, "data", "email", "test_sample_message.eml"), "rb") as email_file:
        email_raw_data = email_file.read()
    raw_email_string = email_raw_data.decode("utf-8")
    email_message = email.message_from_string(raw_email_string)
    data = NotificationData.init_from_emailmessage(email_message)
    assert isinstance(data, NotificationData)
    assert len(data.data_parts) == 5


def test_init_from_emailmessage_with_issue():
    """Test the init_data_emailmessage function with issue."""
    data = NotificationData.init_from_emailmessage("")
    assert data is None
