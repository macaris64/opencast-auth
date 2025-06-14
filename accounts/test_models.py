import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from .models import User


@pytest.mark.django_db
class TestUserModel:
    """Test cases for User model."""
    
    def test_create_user_with_email(self):
        """
        Given: Valid user data
        When: Creating a new user with email
        Then: User should be created successfully
        """
        user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.check_password("testpass123")
        assert user.is_active
        assert not user.is_staff
        assert not user.is_superuser
    
    def test_create_superuser(self):
        """
        Given: Valid superuser data
        When: Creating a superuser
        Then: Superuser should be created with correct permissions
        """
        user = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="adminpass123"
        )
        
        assert user.email == "admin@example.com"
        assert user.username == "admin"
        assert user.is_active
        assert user.is_staff
        assert user.is_superuser
    
    def test_user_string_representation(self):
        """
        Given: A user instance
        When: Converting to string
        Then: Should return email address
        """
        user = User(email="test@example.com", username="testuser")
        assert str(user) == "test@example.com"
    
    def test_user_full_name_property(self):
        """
        Given: A user with first and last name
        When: Accessing full_name property
        Then: Should return combined name
        """
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="John",
            last_name="Doe"
        )
        assert user.full_name == "John Doe"
    
    def test_user_full_name_empty(self):
        """
        Given: A user without names
        When: Accessing full_name property
        Then: Should return empty string
        """
        user = User(email="test@example.com", username="testuser")
        assert user.full_name == ""
    
    def test_email_unique_constraint(self):
        """
        Given: An existing user with email
        When: Creating another user with same email
        Then: Should raise IntegrityError
        """
        User.objects.create_user(
            email="test@example.com",
            username="testuser1",
            password="testpass123"
        )
        
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email="test@example.com",
                username="testuser2",
                password="testpass123"
            )
    
    def test_username_field_is_email(self):
        """
        Given: User model configuration
        When: Checking USERNAME_FIELD
        Then: Should be 'email'
        """
        assert User.USERNAME_FIELD == "email"
    
    def test_required_fields(self):
        """
        Given: User model configuration
        When: Checking REQUIRED_FIELDS
        Then: Should include 'username'
        """
        assert "username" in User.REQUIRED_FIELDS 