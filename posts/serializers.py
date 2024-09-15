from rest_framework import serializers
# from profiles.pagination import CustomPageNumberPagination
from profiles.models import Profile
from profiles.serializers import ProfileSerializer
from .models import Post, Comment, Like, HiddenPost
from django.conf import settings
from urllib.parse import urljoin

class PostCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'user', 'content', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'user', 'created_at']
        read_only_fields = ['user', 'created_at', 'updated_at']


class PostSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    profile_id = serializers.ReadOnlyField(source='user.profile.id')
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Post
        # fields = ['id', 'user', 'profile_id', 'username', 'image', 'content', 'created_at', 'updated_at', 'comments_count', 'likes_count','liked']
        fields = ['id', 'user', 'profile_id', 'username', 'content', 'created_at', 'updated_at', 'comments_count','image_key', 'likes_count','liked', 'image_url']

        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_comments_count(self, obj):
        return obj.get_comments_count()

    def get_likes_count(self, obj):
        return obj.get_likes_count()

    def get_liked(self, obj):
        """Does post liked by auth user or not"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return obj.post_likes.filter(user=request.user).exists()
        return False
    
    def get_image_url(self, obj):
        """Generate the full URL for the image"""
        if obj.image_key:
            return urljoin(settings.MEDIA_URL, obj.image_key)
        return None


class LikerSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ('profile',)


class HiddenPostSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = HiddenPost
        fields = ('post_id',)

    def validate_post_id(self, value):
        if not Post.objects.filter(id=value).exists():
            raise serializers.ValidationError("Post does not exist.")
        return value
