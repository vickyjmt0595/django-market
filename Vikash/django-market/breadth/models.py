import hashlib

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

# Create your models here.
class UploadFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(null=True, unique=True, blank=True)
    checksum = models.CharField(max_length=64,unique=True,null=True, editable=False)

    def __str__(self):
        return str(self.file)
    
    def save(self, *args, **kwargs):
        if self.file and not self.checksum:
            self.checksum = self.calculate_checksum()

        # Check if a file with the same checksum already exists
        if UploadFile.objects.filter(checksum=self.checksum).exists():
            raise ValidationError("This file has already been uploaded.")
        
        if not self.slug:
            self.slug = f"breadth_{self.file.name}"
            self.slug = slugify(self.slug)  # Ensure it's URL-friendly
            # kwargs['force_insert'] = False  # Prevent duplicate insertions
        super().save(*args, **kwargs) # Save 

    def calculate_checksum(self):
        hasher = hashlib.sha256()
        if self.file:
            for chunk in self.file.chunks():
                hasher.update(chunk)
        return hasher.hexdigest()