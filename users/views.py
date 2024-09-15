from urllib.parse import urljoin
import uuid
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from profiles.pagination import CustomPageNumberPagination

from .tasks import send_password_reset_email_task, create_profile_for_new_user
from users.models import CustomUser, BlockedUser
from .serializers import UserRegistrationSerializer, LoginSerializer, ResetPasswordSerializer, CheckCodeSerializer, ConfirmPasswordSerializer, BlockedUserSerializer
from django.contrib.auth import authenticate


class RegisterUserAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # The client should send the avatar_key received from pre-signed URL generation
            avatar_key = request.data.get('avatar_key', None)
            if avatar_key:

                create_profile_for_new_user.delay(user.id, avatar_key)
            else:
                create_profile_for_new_user.delay(user.id)
            user_data = {
                "response": "Successfully registered new user.",
                "email": user.email,
                "username": user.username
            }
            return Response(user_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)

            if user:
                
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': {
                        'username': user.username,
                        'id': user.id,
                        'avatar_url': urljoin(settings.MEDIA_URL, user.avatar_key) if user.avatar_key else None,
                        'is_staff': user.is_staff,
                        'is_active': user.is_active,
                        'phone_number': user.phone_number,
                        'profile_id': user.profile.id 
                    }
                })
            else:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    # Rate limiting
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            try:
                user = CustomUser.objects.get(email=email)
                user.generate_otp()  # Generate OTP and send email
                send_password_reset_email_task.delay(user.email, user.last_otp)
                return Response({"success": True}, status=status.HTTP_200_OK)
            except CustomUser.DoesNotExist:
                return Response({"success": False, "message": "The account was not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckCodeView(APIView):

    def post(self, request):
        serializer = CheckCodeSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"success": True}, status=status.HTTP_200_OK)
        return Response({"success": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ConfirmPasswordView(APIView):

    def post(self, request):
        serializer = ConfirmPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": True}, status=status.HTTP_200_OK)

        return Response({"success": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class BlockUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        user_to_block = get_object_or_404(CustomUser, id=user_id)
        if user_to_block == request.user:
            return Response({'error': 'Cannot block yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        if BlockedUser.objects.filter(blocker=request.user, blocked=user_to_block).exists():
            return Response({'error': 'User already blocked.'}, status=status.HTTP_400_BAD_REQUEST)

        BlockedUser.objects.create(blocker=request.user, blocked=user_to_block)
        return Response({'status': 'User blocked.'}, status=status.HTTP_200_OK)


class UnblockUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        user_to_unblock = get_object_or_404(CustomUser, id=user_id)
        blocked_user = BlockedUser.objects.filter(blocker=request.user, blocked=user_to_unblock).first()
        if not blocked_user:
            return Response({'error': 'User not blocked.'}, status=status.HTTP_400_BAD_REQUEST)

        blocked_user.delete()
        return Response({'status': 'User unblocked.'}, status=status.HTTP_200_OK)


class BlockedListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get(self, request):
        blocked_users = BlockedUser.objects.filter(blocker=request.user)
        serializer = BlockedUserSerializer(blocked_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)