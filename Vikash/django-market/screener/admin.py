from django.contrib import admin
from .models import ScreenerFileUpload , Stock, AddScreener
# Register your models here.
@admin.register(ScreenerFileUpload)
class ScreenerAdmin(admin.ModelAdmin):
    pass


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    pass

@admin.register(AddScreener)
class AddScreenerAdmin(admin.ModelAdmin):
    pass