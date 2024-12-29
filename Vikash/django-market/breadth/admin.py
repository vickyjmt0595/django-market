from django.contrib import admin
from .models import UploadFile

# Register your models here.
@admin.register(UploadFile)
class ModelUpload(admin.ModelAdmin):
    pass    
