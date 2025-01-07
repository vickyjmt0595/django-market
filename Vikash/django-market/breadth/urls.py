from django.urls import path
from . import views

urlpatterns = [

    path('', views.home, name='home'),
    path('breadth-upload/', views.upload_file_view, name='upload_file'),
    path('api/breadth-upload/', views.FileUploadView.as_view(),
         name='file-upload-api'),
    path('analysis-on-db', views.analysis_on_db_data,
         name='analysis_on_db_data'),
    path('breadth-analysis/<slug:slug>',views.breadth_analysis_view,
          name='breadth_analysis_view')
]