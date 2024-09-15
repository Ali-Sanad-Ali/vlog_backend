from django.urls import path
from .views import VlogListView, VlogCreateView, VlogProcessingStatusView, VlogDetailView, VlogUpdateView, VlogDeleteView, CommentListView, CommentCreateView, CommentDetailView, CommentUpdateView, CommentDeleteView, ToggleLikeView, VlogLikersList
urlpatterns = [
    path('vlogs/', VlogListView.as_view(), name='video-list'),
    path('vlogs/create/', VlogCreateView.as_view(), name='Vlog-create'),
    path('vlogs/<int:pk>/status/', VlogProcessingStatusView.as_view(), name='video-processing-status'),
    path('vlogs/<int:pk>/', VlogDetailView.as_view(), name='Vlog-detail'),
    path('vlogs/<int:pk>/update/', VlogUpdateView.as_view(), name='Vlog-update'),
    path('vlogs/<int:pk>/delete/', VlogDeleteView.as_view(), name='Vlog-delete'),
    # Comment URLs
    path('vlogs/<int:vlog_id>/comments/', CommentListView.as_view(), name='comment-list'),
    path('vlogs/<int:vlog_id>/comments/create/', CommentCreateView.as_view(), name='comment-create'),
    path('vlogs/<int:vlog_id>/comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
    path('vlogs/<int:vlog_id>/comments/<int:pk>/update/', CommentUpdateView.as_view(), name='comment-update'),
    path('vlogs/<int:vlog_id>/comments/<int:pk>/delete/', CommentDeleteView.as_view(), name='comment-delete'),
    # Like URLs
    path('vlogs/<int:vlog_id>/toggle-like/', ToggleLikeView.as_view(), name='like-create'),
    path('vlogs/<int:pk>/likers/', VlogLikersList.as_view(), name='video-likers-list'),
]
