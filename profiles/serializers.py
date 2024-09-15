# profiles/serializers.py

from django.conf import settings
from rest_framework import serializers
from urllib.parse import urljoin
from posts.models import Post
from .models import Profile, Follow
from users.tasks import update_profile_avatar


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    # avatar = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    posts_count = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    vlogs_count = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    background_pic_url = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'username', 'bio', 'avatar_url', 'background_pic_url', 'is_following', 'followers_count', 'following_count', 'posts_count', 'vlogs_count',
            'created_at', 'updated_at'
        ]

    def get_posts_count(self, profile):
        return Post.objects.filter(user=profile.user).count()

    def get_followers_count(self, profile):
        if profile.user:
            return profile.user.followers.count()
        return 0

    def get_following_count(self, profile):
        if profile.user:
            return profile.user.following.count()
        return 0

    def get_vlogs_count(self, profile):
        if profile.user:
            return profile.user.vlogs.count()
        return 0

    def get_is_following(self, profile):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(follower=request.user, following=profile.user).exists()
        return False

    def get_avatar_url(self, obj):
        """Generate the full URL for the image"""
        if obj.avatar_key:
            return urljoin(settings.MEDIA_URL, obj.avatar_key)
        return None

    def get_background_pic_url(self, obj):
        """Generate the full URL for the background_pic"""
        if obj.background_pic_key:
            return urljoin(settings.MEDIA_URL, obj.background_pic_key)
        return None


class ProfileUpdateSerializer(serializers.ModelSerializer):
    

    class Meta:
        model = Profile
        # fields = ['bio', 'avatar', 'background_pic']
        fields = ['bio', 'avatar_key', 'background_pic_key']

    def update(self, instance, validated_data):

        avatar_key = validated_data.pop('avatar_key', None)
        background_pic_key = validated_data.pop('background_pic_key', None)
        # Update profile instance with new data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        # Check if the avatar is updated and trigger the Celery task
        # if 'avatar' in validated_data:
        #     user_id = instance.user.id
        #     update_profile_avatar.delay(user_id)
        if avatar_key:
            # avatar_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{avatar_key}"
            instance.avatar_key = avatar_key
            instance.save()

            user_id = instance.user.id
            update_profile_avatar.delay(user_id, avatar_key)
        if background_pic_key:
            # background_pic_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{background_pic_key}"

            instance.background_pic_key = background_pic_key
            instance.save()    
        return instance


class FollowSerializer(serializers.ModelSerializer):
    follower = serializers.CharField(source='follower.username', read_only=True)
    following = serializers.CharField(source='following.username', read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']