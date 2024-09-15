from django.urls import path
from .views import (
    PostListView, PostDetailView, PostCreateView, PostUpdateView, PostDeleteView,
    CommentListView, CommentCreateView, CommentDetailView, CommentUpdateView, CommentDeleteView, ToggleLikeView, UserPostsListView, PostLikersList,HideorUnhidePostView,
)
urlpatterns = [
    # Post URLs
    path('posts/', PostListView.as_view(), name='post-list'),
    # path('posts/generate-presigned-url/', GeneratePresignedUrlView.as_view(), name='generate-presigned-url'),
    path('posts/create/', PostCreateView.as_view(), name='post-create'),
    path('posts/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('posts/<int:pk>/update/', PostUpdateView.as_view(), name='post-update'),
    path('posts/<int:pk>/delete/', PostDeleteView.as_view(), name='post-delete'),
    path('posts/profile/<int:user_id>/', UserPostsListView.as_view(), name='profile-posts'),
    path('posts/<int:post_id>/likers/', PostLikersList.as_view(),name='post-likers-list'),
    path('posts/<int:post_id>/toggle-hide/', HideorUnhidePostView.as_view(), name='hide-post'),
    # Comment URLs
    path('posts/<int:post_id>/comments/', CommentListView.as_view(), name='comment-list'),
    path('posts/<int:post_id>/comments/create/', CommentCreateView.as_view(), name='comment-create'),
    path('posts/<int:post_id>/comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
    path('posts/<int:post_id>/comments/<int:pk>/update/', CommentUpdateView.as_view(), name='comment-update'),
    path('posts/<int:post_id>/comments/<int:pk>/delete/', CommentDeleteView.as_view(), name='comment-delete'),

    #like URLs
    path('posts/<int:post_id>/toggle-like/', ToggleLikeView.as_view(), name='like-create'),
]
