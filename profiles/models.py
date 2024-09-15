from django.db import models
from django.conf import settings
from users.models import CustomUser


class Profile( models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    # avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    avatar_key = models.CharField(max_length=255)
    # background_pic = models.ImageField(upload_to='backgrounds/', null=True, blank=True)
    background_pic_key = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username


class Follow(models.Model):
    follower = models.ForeignKey(CustomUser, related_name='following', on_delete=models.CASCADE,null=True)
    following = models.ForeignKey(CustomUser, related_name='followers', on_delete=models.CASCADE,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.follower.username} follows {self.following.username}'
