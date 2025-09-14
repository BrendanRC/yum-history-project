from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/yum-history/', views.get_yum_history, name='yum_history_api'),
    path('api/sync-s3/', views.sync_from_s3, name='sync_s3'),
]
