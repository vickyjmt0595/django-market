from django.core.management.base import BaseCommand
from screener.models import ScreenerFileUpload  # Replace 'breadth' with your app name

class Command(BaseCommand):
    help = 'Delete all uploaded files from the database'

    def handle(self, *args, **kwargs):
        deleted_count, _ = ScreenerFileUpload.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"Successfully deleted {deleted_count} uploaded files."))
