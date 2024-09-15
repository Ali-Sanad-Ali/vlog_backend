
import logging
from celery import shared_task
from profiles.models import Profile
from django.contrib.auth import get_user_model
from django.core.mail import send_mail


logger = logging.getLogger(__name__)

@shared_task
def create_profile_for_new_user(user_id, avatar_key=None):
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
        profile, created = Profile.objects.get_or_create(user=user)
        if avatar_key:
       
            profile.avatar_key = avatar_key
            profile.save()
            logger.info(f"***Avatar updated for user {user_id}: {user.avatar_key}")
        else:
            logger.info(f"Avatar is missing for user {user_id}")
    except User.DoesNotExist:
        print(f"User with ID {user_id} does not exist")        

@shared_task
def update_profile_avatar(user_id, avatar_key=None):
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
        profile = Profile.objects.get(user=user)
        if avatar_key:
            user.avatar_key = avatar_key
            user.save()

            logger.info(f"Profile avatar updated for user ID {user_id}.Avatar")
        else:
            logger.info(f"No avatar update needed for user ID {user_id}.")    
    except Profile.DoesNotExist:
        # Handle the case where the profile does not exist
        print(f"Profile for user ID {user_id} does not exist")

@shared_task
def send_password_reset_email_task(email, last_otp):
    mail_subject = 'Reset your password'
    message = f"""
    Hi {email},

    We received a request to reset your password. Your OTP code is:

    {last_otp}

    This code is valid for 10 minutes. If you didn't request a password reset, you can ignore this email.

    Thanks,
    Your team
    """
    send_mail(mail_subject, message, 'admin@mywebsite.com', [email])