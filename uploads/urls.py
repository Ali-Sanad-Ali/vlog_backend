from django.urls import path
from .views import GetPresignedURLAPIView

urlpatterns = [
    path('uploads/generate-presigned-url/', GetPresignedURLAPIView.as_view(), name='generate-presigned-url'),
]
