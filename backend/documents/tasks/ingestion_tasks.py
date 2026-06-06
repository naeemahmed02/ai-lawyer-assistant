# from celery import shared_task


# @shared_task
# def process_document_task(document_id: str):
#     """
#     Background task for document ingestion.
#     """

#     from documents.services.ingestion.ingestion_pipeline import DocumentIngestionPipeline
#     pipeline = DocumentIngestionPipeline()

#     pipeline.run(document_id=document_id)


from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(
    bind=True,  # Allows access to 'self' to call self.retry
    max_retries=5,  # Retry up to 5 times before giving up
    default_retry_delay=15,  # Start with a 15-second delay on the first retry
    autoretry_for=(Exception,),  # Catch exceptions to process them inside the task
    exponential_backoff=True,  # Automatically increase wait time (15s, 30s, 60s...)
    retry_jitter=True,  # Add a slight random delay so multiple tasks don't hit the API at the exact same millisecond
)
def process_document_task(self, document_id: str):
    """
    Background task for document ingestion with built-in 429 rate-limit handling.
    """
    from documents.services.ingestion.ingestion_pipeline import (
        DocumentIngestionPipeline,
    )

    try:
        pipeline = DocumentIngestionPipeline()
        pipeline.run(document_id=document_id)

    except Exception as exc:
        # Check if the error message is a Gemini API Quota/Rate Limit error
        error_msg = str(exc)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            logger.warning(
                f"Rate limit hit for document {document_id}. "
                f"Retrying attempt {self.request.retries + 1}/5..."
            )
            # Re-raise the exception through Celery's retry system
            raise self.retry(exc=exc)

        # If it's a completely different error (like a database or syntax error), fail immediately
        logger.error(
            f"Ingestion failed for document {document_id} due to a non-quota error."
        )
        raise exc
