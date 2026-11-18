import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class NestJSPublishingService:
    """Publishes generated work-item hierarchies through the NestJS API."""

    def __init__(self):
        self.base_url = settings.nestjs_api_url.rstrip("/")
        self.timeout = settings.nestjs_publish_timeout

    async def publish_generated_work_items(
        self,
        proposal: dict[str, Any],
        publish_id: str,
    ) -> dict[str, Any]:
        """
        Send a generated work-item hierarchy to NestJS.

        The same publish_id must be reused when retrying
        the same publishing operation.
        """

        endpoint = f"{self.base_url}/work-items/publish-generated"

        payload = {
            "publishId": publish_id,
            "requested_type": proposal["requested_type"],
            "items": proposal["items"],
            "parent_reference": proposal.get("parent_reference"),
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
            ) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                )

                response.raise_for_status()

                result = response.json()

                if not isinstance(result, dict):
                    raise ValueError("NestJS returned an invalid publishing response.")

                logger.info(
                    "Work-item publishing completed. " "Publish ID: %s, Status: %s",
                    publish_id,
                    result.get("status"),
                )

                return result

        except httpx.TimeoutException:
            logger.exception(
                "NestJS publishing request timed out. Publish ID: %s",
                publish_id,
            )

            return {
                "success": False,
                "status": "failed",
                "message": "Publishing request timed out.",
                "created": [],
                "reused": [],
                "errors": [],
                "summary": {
                    "created": 0,
                    "reused": 0,
                    "failed": 0,
                },
            }

        except httpx.HTTPStatusError as error:
            logger.exception(
                "NestJS returned HTTP %s. Publish ID: %s",
                error.response.status_code,
                publish_id,
            )

            return {
                "success": False,
                "status": "failed",
                "message": (
                    f"NestJS publishing failed with HTTP "
                    f"{error.response.status_code}."
                ),
                "created": [],
                "reused": [],
                "errors": [
                    {
                        "message": error.response.text,
                    }
                ],
                "summary": {
                    "created": 0,
                    "reused": 0,
                    "failed": 1,
                },
            }

        except (httpx.RequestError, ValueError, KeyError) as error:
            logger.exception(
                "Unable to publish work items. Publish ID: %s",
                publish_id,
            )

            return {
                "success": False,
                "status": "failed",
                "message": str(error),
                "created": [],
                "reused": [],
                "errors": [
                    {
                        "message": str(error),
                    }
                ],
                "summary": {
                    "created": 0,
                    "reused": 0,
                    "failed": 1,
                },
            }
