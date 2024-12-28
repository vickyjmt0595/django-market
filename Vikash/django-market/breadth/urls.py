from django.urls import path
from . import views

urlpatterns = [

    path('', views.home, name='home'),
    path('upload/', views.upload_file_view, name='upload_file'),
    path('api/upload/', views.FileUploadView.as_view(), name='file-upload-api'),
    path('analysis/<int:file_id>',views.file_analysis_view,
          name='file_analysis_view')
]