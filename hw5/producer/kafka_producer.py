from __future__ import annotations

import logging
from typing import Any

from confluent_kafka import KafkaException
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.serializing_producer import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class KafkaEventProducer:
    def __init__(self, bootstrap_servers: str, schema_registry_url: str, topic: str, schema_str: str) -> None:
        self._topic = topic
        schema_registry_client = SchemaRegistryClient({"url": schema_registry_url})
        value_serializer = AvroSerializer(
            schema_registry_client,
            schema_str,
            lambda value, _: value,
            conf={"auto.register.schemas": False},
        )
        self._producer = SerializingProducer(
            {
                "bootstrap.servers": bootstrap_servers,
                "acks": "all",
                "enable.idempotence": True,
                "key.serializer": StringSerializer("utf_8"),
                "value.serializer": value_serializer,
            }
        )

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        reraise=True,
    )
    def send_with_retry(self, event_dict: dict[str, Any], user_id: str) -> None:
        delivery_state: dict[str, Exception | None] = {"error": None}

        def on_delivery(error, _message) -> None:
            delivery_state["error"] = error

        logger.info("Sending event %s for user %s", event_dict["event_id"], user_id)
        self._producer.produce(
            topic=self._topic,
            key=user_id,
            value=event_dict,
            on_delivery=on_delivery,
        )
        self._producer.poll(0)
        remaining = self._producer.flush(10)
        if remaining != 0:
            raise RuntimeError(f"Producer failed to flush {remaining} queued messages")
        if delivery_state["error"] is not None:
            raise KafkaException(delivery_state["error"])

    def close(self) -> None:
        self._producer.flush(10)
