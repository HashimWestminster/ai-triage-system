# accounts/serializers.py - handles converting user data to/from JSON
# registration, profile, user list, and surgery hours serializers

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SurgeryHours

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """handles patient registration - validates passwords match etc"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    username = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'date_of_birth',
            'nhs_number', 'postal_code', 'role',
        ]
        read_only_fields = ['id']

    def validate(self, data):
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        # dont let random people register as clinicians or admins
        # only actual staff (via django admin) can create privileged accounts
        if validated_data.get('role') in ['clinician', 'care_navigator', 'superuser']:
            request = self.context.get('request')
            if not request or not request.user.is_staff:
                validated_data['role'] = 'patient'

        # auto-generate a username from the email if one wasnt provided
        base_username = validated_data.get('username', validated_data['email'].split('@')[0])
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        validated_data['username'] = username
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """full user profile - used in the /me endpoint and case details"""
    full_name = serializers.SerializerMethodField()
    role_display = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'role_display', 'phone_number',
            'date_of_birth', 'nhs_number', 'postal_code',
            'is_active', 'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_role_display(self, obj):
        return obj.get_role_display()


class UserListSerializer(serializers.ModelSerializer):
    """lighter version for the user management table"""
    full_name = serializers.SerializerMethodField()
    role_display = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'role', 'role_display', 'is_active', 'last_login']

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_role_display(self, obj):
        return obj.get_role_display()


class SurgeryHoursSerializer(serializers.ModelSerializer):
    """serializer for the surgery hours config"""
    day_name = serializers.SerializerMethodField()

    class Meta:
        model = SurgeryHours
        fields = ['id', 'day_of_week', 'day_name', 'open_time', 'close_time', 'is_closed']

    def get_day_name(self, obj):
        return obj.get_day_of_week_display()
