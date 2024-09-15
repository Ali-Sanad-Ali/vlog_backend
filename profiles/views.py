from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from django.core.cache import cache
from .models import Profile, Follow
from users.models import CustomUser, BlockedUser
from .serializers import ProfileSerializer, ProfileUpdateSerializer, FollowSerializer
from .pagination import CustomPageNumberPagination
from rest_framework.permissions import IsAuthenticated


class ProfilesListView(generics.ListAPIView):

    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        """
        Filter out blocked profiles for authenticated users.
        """
        queryset = Profile.objects.all().order_by('-created_at')
        user = self.request.user

        # cache_key = f'profiles_list_{user.id}'
        # queryset = cache.get(cache_key)
        # if not queryset:
        queryset = Profile.objects.all().order_by('-created_at')
        if user.is_authenticated:
            blocked_users = BlockedUser.objects.filter(blocker=user).values_list('blocked', flat=True)
            blocked_by_users = BlockedUser.objects.filter(blocked=user).values_list('blocker', flat=True)
            users_to_exclude = list(set(blocked_users).union(set(blocked_by_users)))
            queryset = Profile.objects.exclude(user__in=users_to_exclude)
            queryset = queryset.order_by('-created_at')
            # Cache the queryset
            # cache.set(cache_key, queryset, timeout=3600)
        return queryset


class ProfileDetailView(generics.RetrieveAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Retrieve the profile for the authenticated user
        return get_object_or_404(Profile, user=self.request.user)


class ProfileUpdateView(generics.UpdateAPIView):
    serializer_class = ProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Retrieve the profile for the authenticated user
        return Profile.objects.get(user=self.request.user)


class FollowUserView(generics.CreateAPIView):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]
    queryset = Follow.objects.all()

    def post(self, request, *args, **kwargs):
        follower = request.user
        following_id = self.kwargs.get('pk')

        try:
            following = CustomUser.objects.get(pk=following_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        # validate
        if follower == following:
            return Response({'error': 'Cannot follow yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        follow, created = Follow.objects.get_or_create(follower=follower, following=following)
        if not created:
            return Response({'error': 'You are already following this user.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = FollowSerializer(follow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UnfollowUserView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Follow.objects.all()
    
    def delete(self, request, *args, **kwargs):
        follower = request.user
        following_id = self.kwargs.get('pk')

        try:
            following = CustomUser.objects.get(pk=following_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        follow = Follow.objects.filter(follower=follower, following=following)
        if not follow.exists():
            return Response({'error': 'You are not following this user.'}, status=status.HTTP_400_BAD_REQUEST)

        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowersListAPIView(generics.ListAPIView):
    serializer_class = ProfileSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs.get('pk')
        request_user = self.request.user
        cache_key = f'followers_{user_id}_page_{self.request.query_params.get("page", 1)}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        try:
    
            user = CustomUser.objects.get(pk=user_id)
            # followers = user.followers.exclude(follower__in=BlockedUser.objects.filter(blocker=request_user).values_list('blocked', flat=True))
            followers = user.followers.all().values_list('follower', flat=True)
            blocked_users = BlockedUser.objects.filter(blocker=request_user).values_list('blocked', flat=True)
            followers = [follower for follower in followers if follower not in blocked_users]
            profiles = Profile.objects.filter(user__in=followers)
            cache.set(cache_key, profiles, timeout=60*15)  # Cache for 15 minutes
            return profiles
        except CustomUser.DoesNotExist:
            return Profile.objects.none()


class FollowingListAPIView(generics.ListAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        user_id = self.kwargs.get('pk')
        request_user = self.request.user

        cache_key = f'following_{user_id}_page_{self.request.query_params.get("page", 1)}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        try:
            user = CustomUser.objects.get(pk=user_id)
            # Get list of following user IDs
            followings = user.following.all().values_list('following', flat=True)
            # Get list of blocked user IDs
            blocked_users = BlockedUser.objects.filter(blocker=request_user).values_list('blocked', flat=True)
            # Filter out blocked users from followings list
            followings = [following for following in followings if following not in blocked_users]
            # Return profiles of all users being followed
            profiles = Profile.objects.filter(user__in=followings)
            cache.set(cache_key, profiles, timeout=60*15)  # Cache for 15 minutes
            Profile.objects.filter(user__in=followings)
            return profiles
        except CustomUser.DoesNotExist:
            return Profile.objects.none()
