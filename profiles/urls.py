from django.urls import path
from .views import ProfileDetailView, ProfileUpdateView, ProfilesListView, FollowUserView, UnfollowUserView, FollowersListAPIView, FollowingListAPIView

urlpatterns = [
    path('profile/', ProfileDetailView.as_view(), name='profile-detail'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
    path('profiles/', ProfilesListView.as_view(), name='user-profile-list'),

    # following endpoints
    path('profile/follow/<int:pk>/', FollowUserView.as_view(), name='follow-user'),
    path('profile/unfollow/<int:pk>/', UnfollowUserView.as_view(), name='unfollow-user'),
    path('profile/followings/<int:pk>/', FollowingListAPIView.as_view(), name='unfollow-user'),
    path('profile/followers/<int:pk>/', FollowersListAPIView.as_view(), name='unfollow-user'),


]
