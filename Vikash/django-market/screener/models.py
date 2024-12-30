from django.db import models
from django.urls import reverse

# Create your models here.
class ScreenerUpload(models.Model):
    file = models.FileField()
    filename = models.CharField(null=False, max_length=100)

    def __str__(self):
        return self.file.name
    
    def get_absolute_url(self):
        return reverse('screener_analysis',
                       args = [str(self.id)])