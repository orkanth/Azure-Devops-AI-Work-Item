import asyncio
import logging

from app.services.document_ingestion_worker import DocumentIngestionWorker


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    worker = DocumentIngestionWorker()
    await worker.run_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Document ingestion worker stopped.")
