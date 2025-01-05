from django.urls import path
from . import views
from .view import form_view

urlpatterns = [
    path('', views.home, name='screener_home'),
    path('screener_upload', views.screener_upload,
         name='screener_upload'),
    path('screener_analysis/<int:id>', views.screener_analysis,
         name='screener_analysis'),
    path('add_screener_to_db', form_view.add_screener,
         name='add_screener')
]