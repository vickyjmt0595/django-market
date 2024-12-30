from django.contrib import admin
from .models import ScreenerUpload
# Register your models here.
@admin.register(ScreenerUpload)
class ScreenerAdmin(admin.ModelAdmin):
    pass
