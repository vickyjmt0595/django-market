from django.contrib import admin
from .models import UploadFile, MarketBreadth

# Register your models here.
@admin.register(UploadFile)
class ModelUpload(admin.ModelAdmin):
    list_display = ('file', 'checksum','slug')

@admin.register(MarketBreadth)
class MarketBreadthAdmin(admin.ModelAdmin):
    pass

