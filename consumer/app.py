import json
import logging
import os
import signal
import threading

from google.cloud import pubsub_v1


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger("consumer")

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
SUBSCRIPTION_ID = os.getenv(
    "PUBSUB_SUBSCRIPTION_ID",
    "demo-events-sub",
)

MAX_IN_FLIGHT_MESSAGES = int(
    os.getenv("MAX_IN_FLIGHT_MESSAGES", "100")
)

REQUIRED_FIELDS = {
    "event_id",
    "event_type",
    "occurred_at",
    "source",
    "payload",
}


class MessageValidationError(ValueError):
    """Raised when a Pub/Sub event is invalid."""


def parse_message(data):
    """
    Decode and validate a Pub/Sub message.

    Args:
        data: Message data as bytes or a string.

    Returns:
        A validated event dictionary.

    Raises:
        MessageValidationError: If JSON or the event structure is invalid.
    """
    if not isinstance(data, (bytes, bytearray, str)):
        raise MessageValidationError(
            "Message data must be bytes or a string."
        )

    try:
        if isinstance(data, (bytes, bytearray)):
            data = data.decode("utf-8")

        event = json.loads(data)

    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MessageValidationError(
            "Message contains invalid UTF-8 or JSON."
        ) from exc

    if not isinstance(event, dict):
        raise MessageValidationError(
            "The event must be a JSON object."
        )

    missing_fields = REQUIRED_FIELDS - event.keys()

    if missing_fields:
        raise MessageValidationError(
            "Missing required fields: "
            + ", ".join(sorted(missing_fields))
        )

    for field in (
        "event_id",
        "event_type",
        "occurred_at",
        "source",
    ):
        if not isinstance(event[field], str) or not event[field].strip():
            raise MessageValidationError(
                f"Field '{field}' must be a non-empty string."
            )

    if not isinstance(event["payload"], dict):
        raise MessageValidationError(
            "Field 'payload' must be a JSON object."
        )

    return event


def process_event(event):
    """
    Process a validated event.

    This example logs the event. Replace or extend this function
    with database writes or other business logic when required.
    """
    logger.info(
        "Processed event_id=%s event_type=%s source=%s",
        event["event_id"],
        event["event_type"],
        event["source"],
    )


def handle_message(message):
    """
    Parse, process, and acknowledge a Pub/Sub message.

    Malformed messages are logged and acknowledged to avoid
    endless redelivery. Production systems may route them to
    a dead-letter topic instead.
    """
    try:
        event = parse_message(message.data)
        process_event(event)

    except MessageValidationError as exc:
        logger.warning(
            "Rejecting malformed message message_id=%s error=%s",
            getattr(message, "message_id", "unknown"),
            exc,
        )

    except Exception:
        logger.exception(
            "Unexpected processing error message_id=%s",
            getattr(message, "message_id", "unknown"),
        )

        # This sample acknowledges unexpected processing failures.
        # A production pipeline should distinguish transient errors
        # and retry them instead of acknowledging them immediately.

    finally:
        message.ack()


def main():
    if not PROJECT_ID:
        raise ValueError(
            "GCP_PROJECT_ID environment variable is required."
        )

    if MAX_IN_FLIGHT_MESSAGES < 1:
        raise ValueError(
            "MAX_IN_FLIGHT_MESSAGES must be at least 1."
        )

    subscriber = pubsub_v1.SubscriberClient()

    subscription_path = subscriber.subscription_path(
        PROJECT_ID,
        SUBSCRIPTION_ID,
    )

    flow_control = pubsub_v1.types.FlowControl(
        max_messages=MAX_IN_FLIGHT_MESSAGES
    )

    shutdown_event = threading.Event()

    def stop_consumer(signum, frame):
        logger.info("Shutdown signal received.")
        shutdown_event.set()

    signal.signal(signal.SIGTERM, stop_consumer)
    signal.signal(signal.SIGINT, stop_consumer)

    streaming_pull_future = subscriber.subscribe(
        subscription_path,
        callback=handle_message,
        flow_control=flow_control,
    )

    logger.info(
        "Consumer started. Project=%s Subscription=%s",
        PROJECT_ID,
        SUBSCRIPTION_ID,
    )

    try:
        while not shutdown_event.wait(timeout=1):
            pass

    finally:
        streaming_pull_future.cancel()

        try:
            streaming_pull_future.result(timeout=10)
        except Exception:
            pass

        subscriber.close()
        logger.info("Consumer stopped.")


if __name__ == "__main__":
    main()