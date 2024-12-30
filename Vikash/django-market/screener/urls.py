from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='screener_home'),
    path('screener_upload', views.screener_upload,
         name='screener_upload'),
    path('screener_analysis/<int:id>', views.screener_analysis,
         name='screener_analysis')
]