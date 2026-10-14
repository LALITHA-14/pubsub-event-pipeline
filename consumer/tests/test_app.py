import json
import unittest
from unittest.mock import Mock, patch

from app import (
    MessageValidationError,
    handle_message,
    parse_message,
)


def valid_event():
    return {
        "event_id": "evt-123",
        "event_type": "demo.event",
        "occurred_at": "2026-10-11T10:00:00+00:00",
        "source": "pubsub-producer",
        "payload": {
            "message": "Hello",
            "sequence": 1,
        },
    }


class TestParseMessage(unittest.TestCase):

    def test_valid_json_bytes(self):
        event = valid_event()
        data = json.dumps(event).encode("utf-8")

        result = parse_message(data)

        self.assertEqual(result, event)

    def test_valid_json_string(self):
        event = valid_event()

        result = parse_message(json.dumps(event))

        self.assertEqual(result, event)

    def test_invalid_json(self):
        with self.assertRaises(MessageValidationError):
            parse_message(b"{invalid json")

    def test_invalid_utf8(self):
        with self.assertRaises(MessageValidationError):
            parse_message(b"\xff")

    def test_json_array_is_rejected(self):
        with self.assertRaises(MessageValidationError):
            parse_message(b"[]")

    def test_json_string_is_rejected(self):
        with self.assertRaises(MessageValidationError):
            parse_message(b'"hello"')

    def test_missing_required_field(self):
        event = valid_event()
        del event["event_id"]

        with self.assertRaises(MessageValidationError):
            parse_message(json.dumps(event))

    def test_empty_event_id(self):
        event = valid_event()
        event["event_id"] = ""

        with self.assertRaises(MessageValidationError):
            parse_message(json.dumps(event))

    def test_payload_must_be_object(self):
        event = valid_event()
        event["payload"] = "invalid"

        with self.assertRaises(MessageValidationError):
            parse_message(json.dumps(event))

    def test_non_string_source(self):
        event = valid_event()
        event["source"] = 123

        with self.assertRaises(MessageValidationError):
            parse_message(json.dumps(event))

    def test_unsupported_data_type(self):
        with self.assertRaises(MessageValidationError):
            parse_message(123)


class TestHandleMessage(unittest.TestCase):

    @patch("app.process_event")
    def test_valid_message_is_processed_and_acknowledged(
        self,
        mock_process_event,
    ):
        event = valid_event()

        message = Mock()
        message.data = json.dumps(event).encode("utf-8")
        message.message_id = "message-1"

        handle_message(message)

        mock_process_event.assert_called_once_with(event)
        message.ack.assert_called_once()

    @patch("app.process_event")
    def test_malformed_message_is_acknowledged(
        self,
        mock_process_event,
    ):
        message = Mock()
        message.data = b"{invalid json"
        message.message_id = "message-2"

        handle_message(message)

        mock_process_event.assert_not_called()
        message.ack.assert_called_once()

    @patch("app.process_event", side_effect=RuntimeError("processing error"))
    def test_processing_error_is_acknowledged(
        self,
        mock_process_event,
    ):
        message = Mock()
        message.data = json.dumps(valid_event()).encode("utf-8")
        message.message_id = "message-3"

        handle_message(message)

        mock_process_event.assert_called_once()
        message.ack.assert_called_once()


if __name__ == "__main__":
    unittest.main()