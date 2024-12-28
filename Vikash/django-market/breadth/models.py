import hashlib

from django.core.exceptions import ValidationError
from django.db import models

# Create your models here.
class UploadFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    checksum = models.CharField(max_length=64,unique=True,null=True, editable=False)

    def __str__(self):
        return str(self.file)
    
    def save(self, *args, **kwargs):
        self.checksum = self.calculate_checksum()

        # Check if a file with the same checksum already exists
        if UploadFile.objects.filter(checksum=self.checksum).exists():
            raise ValidationError("This file has already been uploaded.")
        super().save(*args, **kwargs)

    def calculate_checksum(self):
        hasher = hashlib.sha256()
        for chunk in self.file.chunks():
            hasher.update(chunk)
        return hasher.hexdigest()