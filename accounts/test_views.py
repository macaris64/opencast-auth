import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


@pytest.mark.django_db
class TestAuthenticationViews:
    """Test cases for authentication views."""
    
    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "password": "testpass123",
            "password_confirm": "testpass123"
        }
    
    def test_user_registration_success(self):
        """
        Given: Valid user registration data
        When: POST to registration endpoint
        Then: User should be created and tokens returned
        """
        url = reverse("accounts:register")
        response = self.client.post(url, self.user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert "user" in response.data
        assert "tokens" in response.data
        assert response.data["user"]["email"] == self.user_data["email"]
        assert User.objects.filter(email=self.user_data["email"]).exists()
    
    def test_user_registration_password_mismatch(self):
        """
        Given: Registration data with password mismatch
        When: POST to registration endpoint
        Then: Should return validation error
        """
        url = reverse("accounts:register")
        data = self.user_data.copy()
        data["password_confirm"] = "differentpass"
        
        response = self.client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password_confirm" in response.data
    
    def test_user_registration_duplicate_email(self):
        """
        Given: Existing user with email
        When: Registering with same email
        Then: Should return validation error
        """
        # Create existing user
        User.objects.create_user(
            email=self.user_data["email"],
            username="existinguser",
            password="somepass"
        )
        
        url = reverse("accounts:register")
        response = self.client.post(url, self.user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_user_login_success(self):
        """
        Given: Valid user credentials
        When: POST to login endpoint
        Then: Should return user data and tokens
        """
        # Create user
        user = User.objects.create_user(
            email=self.user_data["email"],
            username=self.user_data["username"],
            password=self.user_data["password"]
        )
        
        url = reverse("accounts:login")
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }
        
        response = self.client.post(url, login_data)
        
        assert response.status_code == status.HTTP_200_OK
        assert "user" in response.data
        assert "tokens" in response.data
        assert response.data["user"]["email"] == user.email
    
    def test_user_login_invalid_credentials(self):
        """
        Given: Invalid credentials
        When: POST to login endpoint
        Then: Should return authentication error
        """
        url = reverse("accounts:login")
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpass"
        }
        
        response = self.client.post(url, login_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_user_logout_success(self):
        """
        Given: Authenticated user with valid refresh token
        When: POST to logout endpoint
        Then: Should logout successfully
        """
        # Create user and get tokens
        user = User.objects.create_user(
            email=self.user_data["email"],
            username=self.user_data["username"],
            password=self.user_data["password"]
        )
        
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Authenticate client
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        
        url = reverse("accounts:logout")
        logout_data = {"refresh": str(refresh)}
        
        response = self.client.post(url, logout_data)
        
        assert response.status_code == status.HTTP_205_RESET_CONTENT
    
    def test_user_logout_unauthenticated(self):
        """
        Given: Unauthenticated request
        When: POST to logout endpoint
        Then: Should return authentication error
        """
        url = reverse("accounts:logout")
        logout_data = {"refresh": "invalid_token"}
        
        response = self.client.post(url, logout_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_logout_missing_refresh_token(self):
        """
        Given: Authenticated user without refresh token
        When: POST to logout endpoint
        Then: Should return bad request error
        """
        # Create user and authenticate
        user = User.objects.create_user(
            email="test2@example.com",
            username="testuser2",
            password="testpass123"
        )
        
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Authenticate client
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        
        url = reverse("accounts:logout")
        logout_data = {}  # No refresh token
        
        response = self.client.post(url, logout_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "refresh token is required" in response.data["error"]

    def test_user_logout_invalid_refresh_token(self):
        """
        Given: Authenticated user with invalid refresh token
        When: POST to logout endpoint
        Then: Should return bad request error
        """
        # Create user and authenticate
        user = User.objects.create_user(
            email="test3@example.com",
            username="testuser3",
            password="testpass123"
        )
        
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Authenticate client
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        
        url = reverse("accounts:logout")
        logout_data = {"refresh": "invalid_refresh_token"}
        
        response = self.client.post(url, logout_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid refresh token" in response.data["error"]


@pytest.mark.django_db
class TestUserViewSet:
    """Test cases for User ViewSet."""
    
    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )
        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            username="staffuser",
            password="staffpass123",
            is_staff=True
        )
    
    def test_get_current_user_authenticated(self):
        """
        Given: Authenticated user
        When: GET to /users/me/
        Then: Should return current user data
        """
        self.client.force_authenticate(user=self.user)
        
        url = reverse("accounts:user-me")
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == self.user.email
    
    def test_get_current_user_unauthenticated(self):
        """
        Given: Unauthenticated request
        When: GET to /users/me/
        Then: Should return authentication error
        """
        url = reverse("accounts:user-me")
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_users_as_staff(self):
        """
        Given: Staff user
        When: GET to /users/
        Then: Should list all users
        """
        self.client.force_authenticate(user=self.staff_user)
        
        url = reverse("accounts:user-list")
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 2  # At least our test users
    
    def test_list_users_as_regular_user(self):
        """
        Given: Regular user
        When: GET to /users/
        Then: Should be forbidden
        """
        self.client.force_authenticate(user=self.user)
        
        url = reverse("accounts:user-list")
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_update_own_profile(self):
        """
        Given: Authenticated user
        When: PATCH to update own profile
        Then: Should update successfully
        """
        self.client.force_authenticate(user=self.user)
        
        url = reverse("accounts:user-detail", args=[self.user.id])
        update_data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        
        response = self.client.patch(url, update_data)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Refresh user from database
        self.user.refresh_from_db()
        assert self.user.first_name == "Updated"
        assert self.user.last_name == "Name"

    def test_change_password_success(self):
        """
        Given: Authenticated user with valid password data
        When: POST to change_password endpoint
        Then: Should change password successfully
        """
        self.client.force_authenticate(user=self.user)
        
        url = reverse("accounts:user-change-password")
        password_data = {
            "old_password": "testpass123",
            "new_password": "newpass123",
            "new_password_confirm": "newpass123"
        }
        
        response = self.client.post(url, password_data)
        
        assert response.status_code == status.HTTP_200_OK
        assert "Password changed successfully" in response.data["message"]
        
        # Verify password was changed
        self.user.refresh_from_db()
        assert self.user.check_password("newpass123")

    def test_change_password_wrong_old_password(self):
        """
        Given: Authenticated user with wrong old password
        When: POST to change_password endpoint
        Then: Should return validation error
        """
        self.client.force_authenticate(user=self.user)
        
        url = reverse("accounts:user-change-password")
        password_data = {
            "old_password": "wrongpass",
            "new_password": "newpass123",
            "new_password_confirm": "newpass123"
        }
        
        response = self.client.post(url, password_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "old_password" in response.data

    def test_change_password_mismatch(self):
        """
        Given: Authenticated user with password confirmation mismatch
        When: POST to change_password endpoint
        Then: Should return validation error
        """
        self.client.force_authenticate(user=self.user)
        
        url = reverse("accounts:user-change-password")
        password_data = {
            "old_password": "testpass123",
            "new_password": "newpass123",
            "new_password_confirm": "differentpass"
        }
        
        response = self.client.post(url, password_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "new_password_confirm" in response.data

    def test_get_user_organizations(self):
        """
        Given: Authenticated user
        When: GET to user organizations endpoint
        Then: Should return user's organizations
        """
        self.client.force_authenticate(user=self.user)
        
        url = reverse("accounts:user-organizations")
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list) 