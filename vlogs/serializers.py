from urllib.parse import urljoin
from django.conf import settings
from rest_framework import serializers

from profiles.models import Profile
from profiles.serializers import ProfileSerializer
from .models import Vlog, Comment


class VlogSerializer(serializers.ModelSerializer):
    user_id = serializers.ReadOnlyField(source='user.id')
    profile_id = serializers.ReadOnlyField(source='user.profile.id')
    username = serializers.CharField(source='user.username', read_only=True)
    vlog_url = serializers.SerializerMethodField()
    # avatar = serializers.ImageField(source='user.avatar', read_only=True)
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    processing_status = serializers.ReadOnlyField()

    class Meta:
        model = Vlog
        fields = ['id', 'user_id', 'profile_id', 'username',  'title', 'description', 'vlog_url', 'duration', 'thumbnail', 'processing_status', 'like_count', 'comment_count', 'liked', 'created_at', 'updated_at']

    def get_like_count(self, obj):
        return obj.likes_count()

    def get_comment_count(self, obj):
        return obj.comments_count()

    def get_liked(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.vlog_likes.filter(user=request.user).exists()
        return False

    def get_vlog_url(self, obj):
        """Generate the full URL for the image"""
        if obj.vlog_key:
            return urljoin(settings.MEDIA_URL, obj.vlog_key)
        return None


class VlogCreateSerializer(serializers.ModelSerializer):
    vlog_key = serializers.CharField(write_only=True)

    class Meta:
        model = Vlog
        fields = ['id', 'user_id', 'title', 'description', 'vlog_key']


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'vlog', 'user', 'content', 'created_at', 'updated_at']


class VlogLikersSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ('profile',)
