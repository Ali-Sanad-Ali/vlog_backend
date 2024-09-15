from django.urls import path
from .views import BlockUserView, BlockedListView, RegisterUserAPIView, LoginView, PasswordResetRequestView, CheckCodeView, ConfirmPasswordView, UnblockUserView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterUserAPIView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # reset-password endpoints 
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/check-code/', CheckCodeView.as_view(), name='password-reset-check-code'),
    path('password-reset/confirm/', ConfirmPasswordView.as_view(), name='password-reset-confirm'),
    # blocking endpoints
    path('users/<int:user_id>/block/', BlockUserView.as_view(), name='user-block'),
    path('users/<int:user_id>/unblock/', UnblockUserView.as_view(), name='user-unblock'),
    path('users/blocked/', BlockedListView.as_view(), name='blocked-users-list'),
]