from celery import shared_task
import os
import time
from django.conf import settings
from django.core.management import call_command

@shared_task
def cleanup_temporary_documents():
    """
    Celery task to clean up temporary documents
    This can be scheduled to run periodically
    """
    try:
        call_command('cleanup_temp_documents', hours=24)
        return "Document cleanup completed successfully"
    except Exception as e:
        return f"Document cleanup failed: {str(e)}"

@shared_task
def process_document_async(file_path, session_key):
    """
    Process document asynchronously for large files
    """
    try:
    
        from .views import extract_text_from_file, create_document_vector_store
        
        with open(file_path, 'rb') as f:
            text = extract_text_from_file(f)
        
        success = create_document_vector_store(text, session_key)
        
       
        os.remove(file_path)
        
        return {
            'success': success,
            'message': 'Document processed successfully' if success else 'Failed to process document'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error processing document: {str(e)}'
        }

# Celery beat schedule (add to settings.py)
"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-temp-documents': {
        'task': 'your_app.tasks.cleanup_temporary_documents',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
}
"""