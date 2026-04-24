from __future__ import annotations

import json
from pathlib import Path

import httpx


class SchemaRegistryRegistrar:
    def __init__(self, schema_registry_url: str, topic: str, schema_path: Path) -> None:
        self._schema_registry_url = schema_registry_url.rstrip("/")
        self._topic = topic
        self._schema_path = schema_path

    def load_schema(self) -> str:
        return self._schema_path.read_text(encoding="utf-8")

    async def register(self) -> dict[str, object]:
        payload = {
            "schema": self.load_schema(),
            "schemaType": "AVRO",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self._schema_registry_url}/subjects/{self._topic}-value/versions",
                headers={"Content-Type": "application/vnd.schemaregistry.v1+json"},
                content=json.dumps(payload),
            )
            response.raise_for_status()
            return response.json()
