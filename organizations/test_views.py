import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization, Role, Membership

User = get_user_model()


class OrganizationViewSetTests(TestCase):
    """Test cases for OrganizationViewSet."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test users
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        
        self.other_user = User.objects.create_user(
            username="otheruser", 
            email="other@example.com",
            password="testpass123",
        )
        
        # Create test organization
        self.org = Organization.objects.create(
            name="Test Organization",
            slug="test-org",
            description="Test Description",
            created_by=self.user,
        )
        
        # Create test roles
        self.owner_role = Role.objects.create(name="owner", priority=100)
        self.member_role = Role.objects.create(name="member", priority=50)
        
        # Create membership for user (owner)
        Membership.objects.create(
            user=self.user,
            organization=self.org,
            role=self.owner_role,
        )
        
        # Generate JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
    
    def authenticate(self, user=None):
        """Authenticate user."""
        if user is None:
            user = self.user
        
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    
    def test_list_organizations_unauthenticated(self):
        """Test that unauthenticated users cannot list organizations."""
        url = reverse("organizations:organization-list")
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_organizations_authenticated(self):
        """Test listing organizations for authenticated user."""
        self.authenticate()
        
        url = reverse("organizations:organization-list")
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Test Organization"
    
    def test_create_organization_success(self):
        """Test creating organization with valid data."""
        self.authenticate()
        
        url = reverse("organizations:organization-list")
        data = {
            "name": "New Organization",
            "slug": "new-org",
            "description": "New Description",
        }
        
        response = self.client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Organization"
        assert response.data["slug"] == "new-org"
        
        # Verify organization created in database
        org = Organization.objects.get(slug="new-org")
        assert org.created_by == self.user
        
        # Verify user became owner
        membership = Membership.objects.get(user=self.user, organization=org)
        assert membership.role.name == "owner"
    
    def test_create_organization_duplicate_slug(self):
        """Test creating organization with duplicate slug fails."""
        self.authenticate()
        
        url = reverse("organizations:organization-list")
        data = {
            "name": "Another Organization",
            "slug": "test-org",  # Same as existing
            "description": "Another Description",
        }
        
        response = self.client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_retrieve_organization_as_member(self):
        """Test retrieving organization details as member."""
        self.authenticate()
        
        url = reverse("organizations:organization-detail", kwargs={"pk": self.org.pk})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Organization"
        assert "memberships" in response.data
    
    def test_retrieve_organization_as_non_member(self):
        """Test retrieving organization as non-member fails."""
        self.authenticate(self.other_user)
        
        url = reverse("organizations:organization-detail", kwargs={"pk": self.org.pk})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_organization_as_owner(self):
        """Test updating organization as owner."""
        self.authenticate()
        
        url = reverse("organizations:organization-detail", kwargs={"pk": self.org.pk})
        data = {
            "name": "Updated Organization",
            "description": "Updated Description",
        }
        
        response = self.client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Updated Organization"
        assert response.data["description"] == "Updated Description"
    
    def test_update_organization_as_member_fails(self):
        """Test that regular members cannot update organization."""
        # Make user a regular member instead of owner
        membership = Membership.objects.get(user=self.user, organization=self.org)
        membership.role = self.member_role
        membership.save()
        
        self.authenticate()
        
        url = reverse("organizations:organization-detail", kwargs={"pk": self.org.pk})
        data = {"name": "Updated Organization"}
        
        response = self.client.patch(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class MembershipViewSetTests(TestCase):
    """Test cases for MembershipViewSet."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test users
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com", 
            password="testpass123",
        )
        
        self.member = User.objects.create_user(
            username="member",
            email="member@example.com",
            password="testpass123", 
        )
        
        # Create test organization
        self.org = Organization.objects.create(
            name="Test Organization",
            slug="test-org",
            created_by=self.owner,
        )
        
        # Create test roles
        self.owner_role = Role.objects.create(name="owner", priority=100)
        self.member_role = Role.objects.create(name="member", priority=50)
        
        # Create memberships
        self.owner_membership = Membership.objects.create(
            user=self.owner,
            organization=self.org,
            role=self.owner_role,
        )
        
        self.membership = Membership.objects.create(
            user=self.member,
            organization=self.org, 
            role=self.member_role,
        )
    
    def authenticate(self, user):
        """Authenticate user."""
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    
    def test_list_memberships_as_owner(self):
        """Test listing memberships as organization owner."""
        self.authenticate(self.owner)
        
        url = reverse("organizations:membership-list")
        response = self.client.get(url, {"organization": self.org.pk})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # Owner + Member
    
    def test_list_memberships_as_member(self):
        """Test listing memberships as regular member."""
        self.authenticate(self.member)
        
        url = reverse("organizations:membership-list")
        response = self.client.get(url, {"organization": self.org.pk})
        
        assert response.status_code == status.HTTP_200_OK
        # Members can see memberships of their organizations
        assert len(response.data["results"]) == 2
    
    def test_update_membership_role_as_owner(self):
        """Test updating membership role as owner."""
        self.authenticate(self.owner)
        
        admin_role = Role.objects.create(name="admin", priority=80)
        
        url = reverse("organizations:membership-detail", kwargs={"pk": self.membership.pk})
        data = {"role": admin_role.pk}
        
        response = self.client.patch(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"]["name"] == "admin"
    
    def test_update_membership_role_as_member_fails(self):
        """Test that regular members cannot update membership roles.""" 
        self.authenticate(self.member)
        
        admin_role = Role.objects.create(name="admin", priority=80)
        
        url = reverse("organizations:membership-detail", kwargs={"pk": self.membership.pk})
        data = {"role": admin_role.pk}
        
        response = self.client.patch(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class OrganizationActionsTests(TestCase):
    """Test cases for Organization custom actions."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        
        # Create test organization
        self.org = Organization.objects.create(
            name="Test Organization",
            slug="test-org",
            created_by=self.user,
        )
        
        # Create test roles
        self.owner_role = Role.objects.create(name="owner", priority=100)
        self.member_role = Role.objects.create(name="member", priority=50)
        
        # Create owner membership
        self.membership = Membership.objects.create(
            user=self.user,
            organization=self.org,
            role=self.owner_role,
        )
    
    def authenticate(self):
        """Authenticate user."""
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    
    def test_organization_members_action(self):
        """Test getting organization members."""
        self.authenticate()
        
        url = reverse('organizations:organization-members', kwargs={'pk': self.org.pk})
        response = self.client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1  # Only owner membership
        assert response.data[0]['user']['email'] == self.user.email 