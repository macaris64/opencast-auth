from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users."""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
        ]
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Password fields didn't match."}
            )
        return attrs
    
    def validate_password(self, value):
        """Validate password using Django's validators."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def create(self, validated_data):
        """Create and return a new user."""
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information."""
    
    class Meta:
        model = User
        fields = ["first_name", "last_name"]


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField()
    password = serializers.CharField(style={"input_type": "password"})
    
    def validate(self, attrs):
        """Validate user credentials."""
        email = attrs.get("email")
        password = attrs.get("password")
        
        if email and password:
            user = authenticate(
                request=self.context.get("request"),
                username=email,
                password=password,
            )
            
            if not user:
                raise serializers.ValidationError(
                    "Unable to log in with provided credentials."
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    "User account is disabled."
                )
            
            attrs["user"] = user
            return attrs
        
        raise serializers.ValidationError(
            "Must include 'email' and 'password'."
        )


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing user password."""
    
    old_password = serializers.CharField(style={"input_type": "password"})
    new_password = serializers.CharField(style={"input_type": "password"})
    new_password_confirm = serializers.CharField(style={"input_type": "password"})
    
    def validate(self, attrs):
        """Validate password change."""
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Password fields didn't match."}
            )
        return attrs
    
    def validate_new_password(self, value):
        """Validate new password using Django's validators."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate_old_password(self, value):
        """Validate old password."""
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                "Old password is incorrect."
            )
        return value 