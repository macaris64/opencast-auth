import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from .serializers import (
    UserCreateSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    UserUpdateSerializer
)

User = get_user_model()


@pytest.mark.django_db
class TestUserCreateSerializer:
    """Test cases for UserCreateSerializer."""

    def test_create_user_success(self):
        """Test successful user creation."""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "password": "testpass123",
            "password_confirm": "testpass123"
        }
        
        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid()
        
        user = serializer.save()
        assert user.email == data["email"]
        assert user.username == data["username"]
        assert user.check_password(data["password"])

    def test_password_mismatch(self):
        """Test password confirmation mismatch."""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123",
            "password_confirm": "differentpass"
        }
        
        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "password_confirm" in serializer.errors

    def test_weak_password_validation(self):
        """Test weak password validation."""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "123",  # Too short
            "password_confirm": "123"
        }
        
        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors


@pytest.mark.django_db
class TestLoginSerializer:
    """Test cases for LoginSerializer."""

    def setup_method(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )
        self.factory = APIRequestFactory()

    def test_valid_login(self):
        """Test valid login credentials."""
        data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        request = self.factory.post("/login/")
        serializer = LoginSerializer(data=data, context={"request": request})
        
        assert serializer.is_valid()
        assert serializer.validated_data["user"] == self.user

    def test_invalid_credentials(self):
        """Test invalid login credentials."""
        data = {
            "email": "test@example.com",
            "password": "wrongpass"
        }
        
        request = self.factory.post("/login/")
        serializer = LoginSerializer(data=data, context={"request": request})
        
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors

    def test_inactive_user(self):
        """Test login with inactive user."""
        self.user.is_active = False
        self.user.save()
        
        data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        request = self.factory.post("/login/")
        serializer = LoginSerializer(data=data, context={"request": request})
        
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors

    def test_missing_credentials(self):
        """Test login with missing credentials."""
        data = {"email": "test@example.com"}  # Missing password
        
        request = self.factory.post("/login/")
        serializer = LoginSerializer(data=data, context={"request": request})
        
        assert not serializer.is_valid()


@pytest.mark.django_db
class TestChangePasswordSerializer:
    """Test cases for ChangePasswordSerializer."""

    def setup_method(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="oldpass123"
        )
        self.factory = APIRequestFactory()

    def test_valid_password_change(self):
        """Test valid password change."""
        data = {
            "old_password": "oldpass123",
            "new_password": "newpass123",
            "new_password_confirm": "newpass123"
        }
        
        request = self.factory.post("/change-password/")
        request.user = self.user
        
        serializer = ChangePasswordSerializer(data=data, context={"request": request})
        
        assert serializer.is_valid()

    def test_wrong_old_password(self):
        """Test wrong old password."""
        data = {
            "old_password": "wrongpass",
            "new_password": "newpass123",
            "new_password_confirm": "newpass123"
        }
        
        request = self.factory.post("/change-password/")
        request.user = self.user
        
        serializer = ChangePasswordSerializer(data=data, context={"request": request})
        
        assert not serializer.is_valid()
        assert "old_password" in serializer.errors

    def test_new_password_mismatch(self):
        """Test new password confirmation mismatch."""
        data = {
            "old_password": "oldpass123",
            "new_password": "newpass123",
            "new_password_confirm": "differentpass"
        }
        
        request = self.factory.post("/change-password/")
        request.user = self.user
        
        serializer = ChangePasswordSerializer(data=data, context={"request": request})
        
        assert not serializer.is_valid()
        assert "new_password_confirm" in serializer.errors

    def test_weak_new_password(self):
        """Test weak new password validation."""
        data = {
            "old_password": "oldpass123",
            "new_password": "123",  # Too short
            "new_password_confirm": "123"
        }
        
        request = self.factory.post("/change-password/")
        request.user = self.user
        
        serializer = ChangePasswordSerializer(data=data, context={"request": request})
        
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors


@pytest.mark.django_db
class TestUserUpdateSerializer:
    """Test cases for UserUpdateSerializer."""

    def test_update_user_info(self):
        """Test updating user information."""
        user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )
        
        data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        
        serializer = UserUpdateSerializer(user, data=data, partial=True)
        assert serializer.is_valid()
        
        updated_user = serializer.save()
        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "Name" 