import os
import time
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Clean up temporary documents older than 24 hours'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Delete files older than this many hours'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        cutoff_time = time.time() - (hours * 3600)
        
        temp_dir = getattr(settings, 'TEMP_DOCUMENTS_DIR', os.path.join(settings.MEDIA_ROOT, 'temp_documents'))
        
        if not os.path.exists(temp_dir):
            self.stdout.write(self.style.WARNING(f'Temp directory does not exist: {temp_dir}'))
            return
        
        deleted_count = 0
        
        try:
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    
                    if file_mtime < cutoff_time:
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                            self.stdout.write(f'Deleted: {filename}')
                        except OSError as e:
                            self.stderr.write(f'Error deleting {filename}: {e}')
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {deleted_count} temporary files older than {hours} hours')
            )
            
        except Exception as e:
            self.stderr.write(f'Error during cleanup: {e}')