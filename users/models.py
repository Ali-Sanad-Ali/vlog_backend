from datetime import timedelta
import random
import uuid
from django.conf import settings
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager


class CustomUser(AbstractUser):

    # avatar = models.ImageField(upload_to='avatars/', default='avatars/avatar.jpeg', null=True, blank=True)
    avatar_key = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=13, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)
    objects = CustomUserManager()

    class Meta:
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
        ]

    def generate_otp(self):
        self.last_otp = f'{random.randint(100000, 999999):06}'
        self.otp_expiry = timezone.now() + timedelta(minutes=10)
        self.save()


class BlockedUser(models.Model):
    blocker = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocked_users', on_delete=models.CASCADE)
    blocked = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocked_by_users', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')

    def save(self, *args, **kwargs):
        from profiles.models import Follow

        # Handle unfollow on block
        Follow.objects.filter(follower=self.blocker, following=self.blocked).delete()
        Follow.objects.filter(follower=self.blocked, following=self.blocker).delete()
        super().save(*args, **kwargs)
