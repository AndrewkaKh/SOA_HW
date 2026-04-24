from __future__ import annotations

import asyncio
from typing import Any

import boto3
from tenacity import retry, stop_after_attempt, wait_exponential


class S3Client:
    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        region_name: str,
    ) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name,
        )

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        reraise=True,
    )
    def _put_object_sync(self, bucket: str, key: str, body: str) -> dict[str, Any]:
        return self._client.put_object(
            Bucket=bucket,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="application/json",
        )

    async def put_object(self, bucket: str, key: str, body: str) -> dict[str, Any]:
        return await asyncio.to_thread(self._put_object_sync, bucket, key, body)
