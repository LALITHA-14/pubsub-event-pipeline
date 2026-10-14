\# Google Cloud Pub/Sub Event Pipeline



A containerized event-driven messaging pipeline built using Python,

Google Cloud Pub/Sub, Docker, Docker Compose, and automated tests.



\## 1. Overview



The project demonstrates asynchronous communication between a

producer and a consumer using Google Cloud Pub/Sub.



The producer generates JSON events and publishes them to a topic.

The consumer subscribes to the topic through a subscription, validates

the event structure, processes valid messages, and acknowledges messages.



\## 2. Architecture



1\. The producer generates an event.

2\. The producer serializes the event as JSON.

3\. The event is published to a Pub/Sub topic.

4\. Pub/Sub delivers the message to a subscription.

5\. The consumer parses and validates the message.

6\. Valid events are processed and logged.

7\. Malformed events are logged and acknowledged.



\## 3. Project Structure



```text

pubsub-event-pipeline/

├── producer/

│   ├── app.py

│   ├── requirements.txt

│   └── Dockerfile

├── consumer/

│   ├── app.py

│   ├── requirements.txt

│   ├── Dockerfile

│   └── tests/

│       └── test\_app.py

├── .env.example

├── .gitignore

├── docker-compose.yml

└── README.md

