from django.db import models
from django.urls import reverse

# Create your models here.

class AddScreener(models.Model):
    name = models.CharField(max_length=100, unique=True)
    url = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class ScreenerFileUpload(models.Model):
    file = models.FileField()
    screener = models.ForeignKey(AddScreener,
                                 on_delete=models.CASCADE)
    def __str__(self):
        return self.file.name
    
    def get_absolute_url(self):
        return reverse('screener_analysis',
                       args = [str(self.id)])
    
    
class Stock(models.Model):
    date = models.DateField()
    name = models.CharField(max_length=100)
    url = models.CharField(max_length=200, unique=False)
    screener = models.ForeignKey(AddScreener,
                                 on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
    class Meta:
        unique_together = ('date', 'name', 'screener')
