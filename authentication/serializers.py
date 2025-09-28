from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserPreference

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'password_confirm')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        """
        Validate password confirmation and strength.
        """
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        if password != password_confirm:
            raise serializers.ValidationError(
                {'password_confirm': 'Passwords do not match.'}
            )

        # Validate password strength
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({'password': e.messages})

        return attrs

    def create(self, validated_data):
        """
        Create a new user with encrypted password.
        """
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'is_active', 'date_joined', 'last_login'
        )
        read_only_fields = ('id', 'email', 'is_active', 'date_joined', 'last_login')


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change.
    """
    old_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """
        Validate new password confirmation.
        """
        new_password = attrs.get('new_password')
        new_password_confirm = attrs.get('new_password_confirm')

        if new_password != new_password_confirm:
            raise serializers.ValidationError(
                {'new_password_confirm': 'New passwords do not match.'}
            )

        return attrs


class UserPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for user preferences.
    """
    
    class Meta:
        model = UserPreference
        fields = (
            'preferred_genres', 'language', 'include_adult',
            'min_rating', 'max_rating', 'preferred_year_from',
            'preferred_year_to', 'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')

    def validate_min_rating(self, value):
        """
        Validate minimum rating.
        """
        if value < 0 or value > 10:
            raise serializers.ValidationError(
                'Rating must be between 0 and 10.'
            )
        return value

    def validate_max_rating(self, value):
        """
        Validate maximum rating.
        """
        if value < 0 or value > 10:
            raise serializers.ValidationError(
                'Rating must be between 0 and 10.'
            )
        return value

    def validate(self, attrs):
        """
        Validate rating range and year range.
        """
        min_rating = attrs.get('min_rating')
        max_rating = attrs.get('max_rating')
        year_from = attrs.get('preferred_year_from')
        year_to = attrs.get('preferred_year_to')

        if min_rating is not None and max_rating is not None:
            if min_rating > max_rating:
                raise serializers.ValidationError(
                    {'min_rating': 'Minimum rating cannot be greater than maximum rating.'}
                )

        if year_from is not None and year_to is not None:
            if year_from > year_to:
                raise serializers.ValidationError(
                    {'preferred_year_from': 'From year cannot be greater than to year.'}
                )

        return attrs