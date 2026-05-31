from celery import shared_task


@shared_task
def process_document_task(document_id: str):
    """
    Background task for document ingestion.
    """
    
    from documents.services.ingestion.ingestion_pipeline import DocumentIngestionPipeline
    pipeline = DocumentIngestionPipeline()
    
    pipeline.run(document_id=document_id)
    