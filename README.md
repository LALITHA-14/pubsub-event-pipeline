# Google Cloud Pub/Sub Event Pipeline

An event-driven messaging pipeline built with **Python, Google Cloud Pub/Sub, Docker, and Docker Compose**. The system publishes structured JSON events to a Google Cloud Pub/Sub topic and consumes them asynchronously through a subscriber application.

The project demonstrates event-driven architecture, cloud messaging, containerization, message validation, error handling, automated testing, and application logging.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Google Cloud Setup](#google-cloud-setup)
- [Environment Configuration](#environment-configuration)
- [Run the Application](#run-the-application)
- [Verify the Pipeline](#verify-the-pipeline)
- [Testing](#testing)
- [Message Format](#message-format)
- [Containerization and Design Decisions](#containerization-and-design-decisions)
- [Error Handling](#error-handling)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)
- [Future Improvements](#future-improvements)

## Overview

Applications often need to exchange events without requiring the producer and consumer to run synchronously or communicate directly.

This project addresses that requirement using Google Cloud Pub/Sub as a managed messaging service.

The producer generates structured events and publishes them to a Pub/Sub topic. Google Cloud Pub/Sub delivers those events to a subscription, where the consumer receives, validates, and processes them.

The producer and consumer run as separate Docker containers, making the application easier to configure, execute, and maintain.

### Problem Statement

Design and implement a reliable, containerized event-processing pipeline that supports asynchronous communication between event producers and consumers, validates incoming messages, handles malformed data gracefully, and provides clear operational logs.

### Project Objectives

- Implement asynchronous event publishing and consumption.
- Integrate Python applications with Google Cloud Pub/Sub.
- Define and validate a consistent JSON event structure.
- Handle malformed messages without crashing the consumer.
- Containerize applications using Docker and Docker Compose.
- Implement unit tests for message parsing and error handling.
- Provide environment-based configuration and secure credential handling.

## Architecture

```text
                 Event Generation
                        |
                        v
              +-------------------+
              |  Python Producer  |
              |    Container      |
              +-------------------+
                        |
                        | Publish JSON events
                        v
              +-------------------+
              | Google Cloud      |
              | Pub/Sub Topic     |
              |   demo-events     |
              +-------------------+
                        |
                        v
              +-------------------+
              | Pub/Sub           |
              | Subscription      |
              | demo-events-sub   |
              +-------------------+
                        |
                        | Deliver messages
                        v
              +-------------------+
              |  Python Consumer  |
              |    Container      |
              +-------------------+
                        |
                        v
              +-------------------+
              | Validate and      |
              | Process Events    |
              +-------------------+
                        |
                        v
              Structured Logs
```

### Workflow

1. The producer generates an event with a unique event ID, event type, timestamp, source, and payload.
2. The event is serialized into JSON.
3. The producer publishes the event to the configured Google Cloud Pub/Sub topic.
4. Pub/Sub makes the message available through the configured subscription.
5. The consumer receives the message asynchronously.
6. The consumer validates the message structure and required fields.
7. Valid messages are processed and logged.
8. Malformed messages and processing errors are logged and handled by the consumer's callback logic.

The producer and consumer communicate through Pub/Sub rather than directly connecting to one another.

## Features

- **Event-driven communication:** Uses Google Cloud Pub/Sub for asynchronous messaging.
- **Independent services:** Producer and consumer run in separate containers.
- **Structured events:** Uses JSON messages with a consistent schema.
- **Message validation:** Checks required fields, data types, UTF-8 encoding, and JSON structure.
- **Error handling:** Handles malformed messages and logs processing errors.
- **Automated testing:** Includes unit tests for valid messages, invalid JSON, missing fields, and error-handling scenarios.
- **Containerization:** Uses Docker for reproducible application environments.
- **Multi-stage consumer image:** Separates dependency installation from the runtime image.
- **Health checks:** Docker Compose checks configured service health conditions.
- **Configurable execution:** Uses environment variables for project identifiers, topic and subscription names, publishing intervals, and logging.
- **Operational visibility:** Provides structured logs for published and processed events.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Producer, consumer, and test implementation |
| Google Cloud Pub/Sub | Managed messaging and asynchronous event delivery |
| Google Cloud SDK (`gcloud`) | Cloud project configuration and Pub/Sub resource management |
| Docker | Application containerization |
| Docker Compose | Local orchestration of producer and consumer |
| Google Cloud Pub/Sub Python Client | Publishing and subscribing to messages |
| Python `unittest` | Automated unit testing |
| Git and GitHub | Version control and project hosting |

## Project Structure

```text
pubsub-event-pipeline/
│
├── producer/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── consumer/
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/
│       └── test_app.py
│
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

### Directory Responsibilities

**`producer/`**
- Generates structured events.
- Publishes messages to Google Cloud Pub/Sub.
- Logs successful publishing operations and failures.

**`consumer/`**
- Subscribes to the configured Pub/Sub subscription.
- Validates incoming messages.
- Processes valid events and logs errors.
- Contains unit tests for message parsing and callback behavior.

**`docker-compose.yml`**
- Configures the producer and consumer services.
- Supplies runtime environment variables.
- Configures the containers to access the required Google Cloud credentials.
- Defines service health checks.

**`.env.example`**
- Documents the environment variables required to configure the application.

**`.gitignore`**
- Excludes local configuration and sensitive credentials from version control.

## Prerequisites

Install and configure the following before running the project:

1. Python 3.12 or compatible Python environment.
2. Docker Desktop with Docker Compose.
3. Google Cloud CLI.
4. A Google Cloud project with billing and permissions configured as required by your organization's policies.
5. Google Cloud authentication with permission to publish to the topic and consume messages from the subscription.

You can verify the installations using:

```cmd
python --version
docker --version
docker compose version
gcloud --version
git --version
```

The application uses Python 3.12 in its Docker containers.

## Google Cloud Setup

The following commands use the example project and resource names configured for this project.

### 1. Configure the Google Cloud project

```cmd
gcloud auth login
gcloud config set project pubsub-event-pipeline
```

Set up Application Default Credentials for the Python client:

```cmd
gcloud auth application-default login
```

Configure the quota project:

```cmd
gcloud auth application-default set-quota-project pubsub-event-pipeline
```

The authenticated account must have the necessary permissions for the Pub/Sub operations performed by the application.

### 2. Enable the Pub/Sub API

```cmd
gcloud services enable pubsub.googleapis.com --project=pubsub-event-pipeline
```

### 3. Create the Pub/Sub topic

Run this command only if the topic does not already exist:

```cmd
gcloud pubsub topics create demo-events --project=pubsub-event-pipeline
```

### 4. Create the subscription

Run this command only if the subscription does not already exist:

```cmd
gcloud pubsub subscriptions create demo-events-sub --topic=demo-events --project=pubsub-event-pipeline
```

### 5. Verify the resources

Check the topic:

```cmd
gcloud pubsub topics describe demo-events --project=pubsub-event-pipeline
```

Check the subscription:

```cmd
gcloud pubsub subscriptions describe demo-events-sub --project=pubsub-event-pipeline
```

The subscription must reference the `demo-events` topic.

## Environment Configuration

Create a local `.env` file from the provided example.

From the project root, run:

```cmd
copy .env.example .env
```

Open `.env` in a text editor and configure the values for your Google Cloud project and runtime environment.

The project configuration uses the following variables:

| Variable | Purpose |
|---|---|
| `GCP_PROJECT_ID` | Google Cloud project ID |
| `PUBSUB_TOPIC_ID` | Pub/Sub topic used by the producer |
| `PUBSUB_SUBSCRIPTION_ID` | Pub/Sub subscription used by the consumer |
| `GCP_CREDENTIALS_FILE` | Local credentials file path if using that configuration |
| `GOOGLE_APPLICATION_CREDENTIALS_CONTAINER` | Credentials path inside the container if used by the Compose configuration |
| `PUBLISH_INTERVAL_SECONDS` | Delay between publishing events |
| `EVENT_TYPE` | Event type assigned to generated messages |
| `EVENT_SOURCE` | Identifier for the event producer |
| `MAX_IN_FLIGHT_MESSAGES` | Maximum number of outstanding messages configured for the consumer |
| `PUBSUB_EMULATOR_HOST` | Optional Pub/Sub emulator endpoint |
| `LOG_LEVEL` | Application logging level |

Use the variable names and credential paths supported by your current `docker-compose.yml`. In the default Windows setup, the Compose configuration mounts the local Google Cloud Application Default Credentials file into the containers.

**Important:** `.env.example` contains example configuration values. Do not put actual credentials, access tokens, or private keys in it.

## Run the Application

### 1. Clone the repository

After pushing the project to GitHub, clone it using your repository URL:

```cmd
git clone YOUR_GITHUB_REPOSITORY_URL
cd pubsub-event-pipeline
```

### 2. Configure the environment

```cmd
copy .env.example .env
```

Update `.env` with your project configuration. Ensure the credential mount in Docker Compose points to an existing credentials file.

### 3. Build the Docker images

```cmd
docker compose build
```

The consumer uses a multi-stage Docker build to separate dependency installation from the final runtime environment.

### 4. Start the services

```cmd
docker compose up -d
```

Docker Compose starts the producer and consumer in the background.

### 5. Check service status

```cmd
docker compose ps
```

Confirm that both services are running and that their configured health checks pass.

### 6. View producer logs

```cmd
docker compose logs --tail=50 producer
```

Follow the logs continuously:

```cmd
docker compose logs -f producer
```

### 7. View consumer logs

```cmd
docker compose logs --tail=50 consumer
```

Follow the logs continuously:

```cmd
docker compose logs -f consumer
```

### 8. Stop the services

```cmd
docker compose down
```

This stops and removes the Compose-managed containers and network. It does not delete the Google Cloud Pub/Sub topic or subscription.

## Verify the Pipeline

A successful run should demonstrate that the producer publishes events and the consumer processes them.

### Producer output

Example:

```text
INFO producer Producer started. Project=pubsub-event-pipeline Topic=demo-events
INFO producer Published event_id=<event-id> message_id=<message-id>
```

### Consumer output

Example:

```text
INFO consumer Consumer started. Project=pubsub-event-pipeline Subscription=demo-events-sub
INFO consumer Processed event_id=<event-id> event_type=demo.event source=pubsub-producer
```

The event ID in the consumer log should match an event ID published by the producer.

These logs provide evidence that events are being published and delivered through the Pub/Sub pipeline.

## Testing

The project includes unit tests in `consumer/tests/test_app.py`.

The tests cover message parsing, validation, and consumer callback behavior.

### Test coverage

- Valid JSON messages.
- Invalid JSON.
- Invalid UTF-8 data.
- Missing required fields.
- Empty event IDs.
- Invalid field types.
- Non-object JSON values.
- Invalid payload types.
- Unsupported input data types.
- Acknowledgment behavior for valid messages.
- Acknowledgment behavior for malformed messages.
- Handling of unexpected processing errors.

### Run the tests in Docker

From the project root, run:

```cmd
docker run --rm -v "%cd%\consumer:/app" -w /app python:3.12-slim sh -c "pip install --no-cache-dir -r requirements.txt && PYTHONPATH=. python -m unittest discover -s tests -v"
```

A successful test run ends with output similar to:

```text
Ran 14 tests

OK
```

These are unit tests. They do not replace an end-to-end integration test against Google Cloud Pub/Sub.

## Message Format

The producer publishes JSON events with the following structure:

```json
{
  "event_id": "unique-event-id",
  "event_type": "demo.event",
  "occurred_at": "2026-10-14T10:00:00Z",
  "source": "pubsub-producer",
  "payload": {
    "message": "Hello from Google Cloud Pub/Sub"
  }
}
```

### Field descriptions

| Field | Description |
|---|---|
| `event_id` | Unique identifier for the event |
| `event_type` | Category or type of event |
| `occurred_at` | Event timestamp |
| `source` | Application that generated the event |
| `payload` | Object containing event-specific data |

The consumer validates the event structure before processing it.

The `payload` must be a JSON object, and the required string fields must contain non-empty values.

## Containerization and Design Decisions

### Separate producer and consumer services

The producer and consumer are deployed independently in separate containers. This keeps message generation separate from message processing and allows the services to be configured independently.

### Managed messaging

Google Cloud Pub/Sub provides the messaging layer, avoiding the need to implement a custom message broker.

### Multi-stage consumer image

The consumer Dockerfile uses multiple build stages to separate dependency installation from the final runtime image. This helps keep build-time artifacts out of the final image.

### Environment-based configuration

Project identifiers, topic names, subscription names, publishing intervals, and logging settings are configured through environment variables rather than hard-coded throughout the application.

### Health checks

Docker Compose health checks provide basic service-status information. They should not be interpreted as proof that the Google Cloud Pub/Sub service is reachable or that messages are being processed successfully; application logs and integration checks are also needed.

### Automated validation

Unit tests verify the consumer's parsing and error-handling behavior without requiring a live Pub/Sub connection for each test.

## Error Handling

The pipeline includes handling for common message-processing problems.

**Malformed messages:** Invalid UTF-8, invalid JSON, missing required fields, and invalid field types are rejected and logged.

**Processing exceptions:** Unexpected processing errors are logged by the consumer callback.

**Publishing failures:** The producer logs failures encountered while publishing events.

**Operational errors:** Docker Compose status and service logs help identify startup, authentication, and connectivity issues.

The current consumer callback acknowledges malformed messages and handles unexpected processing errors according to its implemented callback logic. A production deployment should consider a dead-letter topic, explicit retry policies, and durable error handling to prevent failed events from being silently lost.

## Troubleshooting

### Docker Desktop is unavailable

If Docker commands return an engine connection error:

1. Open Docker Desktop.
2. Wait until the Docker engine is running.
3. Verify the installation:

```cmd
docker version
docker info
```

4. Retry:

```cmd
docker compose up -d
```

### Authentication errors

Verify the active Google Cloud project:

```cmd
gcloud config get-value project
```

Verify the active account:

```cmd
gcloud auth list
```

Refresh Application Default Credentials if necessary:

```cmd
gcloud auth application-default login
```

Confirm that Docker Compose mounts the expected credentials file and sets `GOOGLE_APPLICATION_CREDENTIALS` to the matching path inside the container.

### Topic or subscription not found

Check the topic:

```cmd
gcloud pubsub topics describe demo-events --project=pubsub-event-pipeline
```

Check the subscription:

```cmd
gcloud pubsub subscriptions describe demo-events-sub --project=pubsub-event-pipeline
```

Verify that the environment variables match the actual resource names.

### Producer publishes but the consumer does not process events

Inspect both services:

```cmd
docker compose logs --tail=100 producer
docker compose logs --tail=100 consumer
```

Check the subscription name, project ID, credentials, IAM permissions, and Pub/Sub connectivity.

### Intermittent publishing timeouts

Inspect the producer logs for `TimeoutError` or other publishing failures. Check network connectivity, credentials, and Pub/Sub availability. A publish timeout does not necessarily establish whether the message was accepted by the service, so production implementations should use appropriate retry behavior and account for possible duplicate events.

### Container status is healthy but the application is failing

Review the service logs. The configured health checks may validate only basic conditions, such as required environment variables, rather than application-level or cloud-service connectivity.

## Security Considerations

- Never commit `.env` files.
- Never commit service-account private keys, access tokens, or other secrets.
- Keep local credential files outside version control.
- Use `.env.example` to document configuration without exposing secrets.
- Grant only the Google Cloud IAM permissions required by each service.
- Prefer short-lived credentials or workload identity mechanisms for production deployments.
- Avoid printing credentials or sensitive event payloads in logs.
- Review Git history if a secret was ever committed; removing the file from the latest commit does not remove it from previous commits.

## Future Improvements

Potential enhancements for a production-oriented implementation include:

- Configure a Pub/Sub dead-letter topic for repeatedly failing messages.
- Implement bounded retry and exponential backoff for publishing failures.
- Improve shutdown handling and graceful cancellation of subscriber callbacks.
- Add end-to-end integration tests against Pub/Sub or the Pub/Sub emulator.
- Introduce structured metrics and dashboards for throughput, failures, and processing latency.
- Add schema versioning and event-contract validation.
- Implement idempotent event processing to handle duplicate deliveries safely.
- Add automated linting, testing, and Docker builds through a CI/CD workflow.
- Deploy the containers to a managed platform such as Google Cloud Run or Google Kubernetes Engine.

## Conclusion

This project demonstrates an end-to-end, event-driven messaging workflow using Python and Google Cloud Pub/Sub. By combining structured event publishing, asynchronous consumption, message validation, Docker containerization, logging, and automated unit testing, it provides a foundation for building cloud-based event-processing systems.

The implementation can be extended with stronger retry policies, dead-letter handling, observability, and managed deployment practices as the requirements grow.
