from celery import shared_task

from backend.documents.services.ingestion.ingestion_pipeline import DocumentIngestionPipeline

@shared_task
def process_document_task(document_id: str):
    """
    Background task for document ingestion.
    """
    
    pipeline = DocumentIngestionPipeline()
    
    pipeline.run(document_id=document_id)
    