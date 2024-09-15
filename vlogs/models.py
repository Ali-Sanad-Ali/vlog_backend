from django.db import models
from users.models import CustomUser
from django.core.validators import FileExtensionValidator


class Vlog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='vlogs')
    vlog_key = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    processing_status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def comments_count(self):
        return self.vlog_comments.count()

    def likes_count(self):
        return self.vlog_likes.count()

    def __str__(self):
        return self.title


class VlogProcessingTask(models.Model):
    PENDING = 'pending'
    FAILED = 'failed'
    COMPLETED = 'completed'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (FAILED, 'Failed'),
        (COMPLETED, 'Completed'),
    ]

    vlog = models.OneToOneField(Vlog, on_delete=models.CASCADE, related_name='processing_task')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    error_message = models.TextField(blank=True, null=True) 

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Comment(models.Model):
    vlog = models.ForeignKey(Vlog, on_delete=models.CASCADE, related_name='vlog_comments')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='vlog_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.user} on {self.vlog}'


class Like(models.Model):
    vlog = models.ForeignKey(Vlog, on_delete=models.CASCADE, related_name='vlog_likes')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='vlog_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('vlog', 'user')

    def __str__(self):
        return f'Like by {self.user} on {self.video}'
