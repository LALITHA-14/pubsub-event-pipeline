import json
import logging
import os
import signal
import time
import uuid
from datetime import datetime, timezone

from google.cloud import pubsub_v1


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger("producer")

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
TOPIC_ID = os.getenv("PUBSUB_TOPIC_ID", "demo-events")
PUBLISH_INTERVAL = float(
    os.getenv("PUBLISH_INTERVAL_SECONDS", "5")
)
EVENT_TYPE = os.getenv("EVENT_TYPE", "demo.event")
EVENT_SOURCE = os.getenv("EVENT_SOURCE", "pubsub-producer")

running = True


def stop_producer(signum, frame):
    """Stop publishing when a termination signal is received."""
    global running
    running = False
    logger.info("Shutdown signal received.")


def create_event(sequence):
    """Create a JSON-compatible event."""
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": EVENT_TYPE,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "source": EVENT_SOURCE,
        "payload": {
            "message": "Hello from the Pub/Sub producer",
            "sequence": sequence,
        },
    }


def publish_event(publisher, topic_path, event):
    """Publish an event and wait for Pub/Sub confirmation."""
    message_data = json.dumps(event).encode("utf-8")

    future = publisher.publish(
        topic_path,
        message_data,
        event_type=event["event_type"],
        event_id=event["event_id"],
    )

    message_id = future.result(timeout=30)

    logger.info(
        "Published event_id=%s message_id=%s",
        event["event_id"],
        message_id,
    )

    return message_id


def main():
    if not PROJECT_ID:
        raise ValueError("GCP_PROJECT_ID environment variable is required.")

    if PUBLISH_INTERVAL <= 0:
        raise ValueError("PUBLISH_INTERVAL_SECONDS must be greater than zero.")

    signal.signal(signal.SIGTERM, stop_producer)
    signal.signal(signal.SIGINT, stop_producer)

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

    sequence = 1

    logger.info(
        "Producer started. Project=%s Topic=%s",
        PROJECT_ID,
        TOPIC_ID,
    )

    try:
        while running:
            event = create_event(sequence)

            try:
                publish_event(publisher, topic_path, event)
            except Exception:
                logger.exception(
                    "Failed to publish event sequence=%s",
                    sequence,
                )

            sequence += 1

            # Sleep in small intervals to respond to shutdown signals.
            remaining = PUBLISH_INTERVAL

            while running and remaining > 0:
                sleep_interval = min(remaining, 0.5)
                time.sleep(sleep_interval)
                remaining -= sleep_interval

    finally:
        logger.info("Stopping producer.")
        publisher.transport.close()


if __name__ == "__main__":
    main()