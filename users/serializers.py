from django.utils import timezone
from rest_framework import serializers
from .models import BlockedUser, CustomUser
from django.contrib.auth.password_validation import validate_password

from profiles.models import Profile
from profiles.serializers import ProfileSerializer


class UserRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    # avatar = serializers.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'avatar_key', 'password', 'password2')
        extra_kwargs = {
            'password': {'write_only': True},       
        }

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        if CustomUser.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'Error': 'Email already exists.'})
        if CustomUser.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({'Error': 'Username already exists.'})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        password2 = validated_data.pop('password2')
        user = CustomUser.objects.create(**validated_data)
        user.set_password(password)  # password hashing
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class CheckCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        try:
            user = CustomUser.objects.get(email=data['email'])
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        if user.last_otp != data['code']:
            raise serializers.ValidationError("Wrong code.")

        if user.otp_expiry < timezone.now():
            raise serializers.ValidationError("Code expired.")

        return data


class ConfirmPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(max_length=128, validators=[validate_password])

    def validate(self, data):
        try:
            user = CustomUser.objects.get(email=data['email'])
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        if user.last_otp != data['code']:
            raise serializers.ValidationError("Wrong code.")
        if user.otp_expiry < timezone.now():
            raise serializers.ValidationError("Code expired.")

        return data

    def save(self):
        email = self.validated_data.get('email')
        new_password = self.validated_data.get('new_password')
        user = CustomUser.objects.get(email=email)
        user.set_password(new_password)
        user.save()


class BlockedUserSerializer(serializers.ModelSerializer):
    """
    return the profiles of  blocked users
    """
    blocked_profile = serializers.SerializerMethodField()

    class Meta:
        model = BlockedUser
        fields = ['blocked_profile']

    def get_blocked_profile(self, obj):
        profiles = Profile.objects.filter(user__in=BlockedUser.objects.values_list('blocked', flat=True))
        profile_dict = {profile.user.id: profile for profile in profiles}
        return ProfileSerializer(profile_dict.get(obj.blocked.id), context=self.context).data
