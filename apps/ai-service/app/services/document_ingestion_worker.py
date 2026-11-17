
import asyncio
import logging

from app.rag.ingestion import DocumentIngestionService
from app.services.nestjs_client import nestjs_client


logger = logging.getLogger(__name__)


class DocumentIngestionWorker:
    """Process document ingestion jobs created by NestJS."""

    def __init__(
        self,
        ingestion_service: DocumentIngestionService | None = None,
        client=None,
    ):
        self.ingestion_service = (
            ingestion_service or DocumentIngestionService()
        )
        self.client = client or nestjs_client

    async def process_next_job(self) -> dict | None:
        """Claim and process one available ingestion job."""

        job = await self.client.claim_ingestion_job()

        if not job:
            return None

        job_id = job["id"]

        try:
            document = job.get("document")

            if not document:
                raise ValueError(
                    f"Ingestion job {job_id} has no document details."
                )

            document_id = document["id"]
            project_id = document["projectId"]
            file_name = document["fileName"]

            logger.info(
                "Processing document %s for job %s",
                document_id,
                job_id,
            )

            # Download original PDF/DOCX bytes from NestJS.
            file_content = await self.client.get_document_content(
                document_id
            )

            # Extract, chunk, embed and persist.
            result = await self.ingestion_service.ingest_document(
                document_id=document_id,
                project_id=project_id,
                file_name=file_name,
                file_content=file_content,
            )

            # Mark job completed only after successful persistence.
            await self.client.complete_ingestion_job(job_id)

            logger.info("Ingestion job %s completed.", job_id)

            return result

        except Exception as exc:
            logger.exception(
                "Document ingestion job %s failed.",
                job_id,
            )

            try:
                await self.client.fail_ingestion_job(
                    job_id,
                    str(exc),
                )
            except Exception:
                logger.exception(
                    "Could not report failure for ingestion job %s.",
                    job_id,
                )

            return {
                "job_id": job_id,
                "status": "failed",
                "error": str(exc),
            }

    async def run_forever(self, poll_interval: float = 5.0) -> None:
        """Continuously poll NestJS for available ingestion jobs."""

        logger.info("Document ingestion worker started.")

        while True:
            try:
                result = await self.process_next_job()

                if result is None:
                    await asyncio.sleep(poll_interval)

            except asyncio.CancelledError:
                logger.info("Document ingestion worker stopped.")
                raise

            except Exception:
                logger.exception("Unexpected ingestion worker error.")
                await asyncio.sleep(poll_interval)
