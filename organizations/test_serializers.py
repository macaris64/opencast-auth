import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from .models import Organization, Role, Membership
from .serializers import (
    OrganizationSerializer,
    OrganizationCreateSerializer,
    RoleSerializer,
    MembershipSerializer,
    MembershipCreateSerializer
)

User = get_user_model()


@pytest.mark.django_db
class TestOrganizationSerializer:
    """Test cases for OrganizationSerializer."""

    def setup_method(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )

    def test_serialize_organization(self):
        """Test organization serialization."""
        org = Organization.objects.create(
            name="Test Org",
            slug="test-org",
            description="Test description",
            created_by=self.user
        )
        
        serializer = OrganizationSerializer(org)
        data = serializer.data
        
        assert data["name"] == "Test Org"
        assert data["slug"] == "test-org"
        assert data["description"] == "Test description"
        assert "members_count" in data


@pytest.mark.django_db
class TestOrganizationCreateSerializer:
    """Test cases for OrganizationCreateSerializer."""

    def setup_method(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )
        self.factory = APIRequestFactory()
        
        # Create required roles
        Role.objects.get_or_create(name="owner", defaults={"priority": 100})
        Role.objects.get_or_create(name="admin", defaults={"priority": 80})
        Role.objects.get_or_create(name="member", defaults={"priority": 50})

    def test_create_organization_success(self):
        """Test successful organization creation."""
        data = {
            "name": "New Org",
            "slug": "new-org",
            "description": "New organization"
        }
        
        request = self.factory.post("/organizations/")
        request.user = self.user
        
        serializer = OrganizationCreateSerializer(
            data=data,
            context={"request": request}
        )
        
        assert serializer.is_valid()
        org = serializer.save()
        
        assert org.name == "New Org"
        assert org.created_by == self.user

    def test_duplicate_slug_validation(self):
        """Test duplicate slug validation."""
        # Create existing organization
        Organization.objects.create(
            name="Existing Org",
            slug="test-org",
            created_by=self.user
        )
        
        data = {
            "name": "New Org",
            "slug": "test-org",  # Duplicate slug
            "description": "New organization"
        }
        
        request = self.factory.post("/organizations/")
        request.user = self.user
        
        serializer = OrganizationCreateSerializer(
            data=data,
            context={"request": request}
        )
        
        assert not serializer.is_valid()
        assert "slug" in serializer.errors


@pytest.mark.django_db
class TestRoleSerializer:
    """Test cases for RoleSerializer."""

    def test_serialize_role(self):
        """Test role serialization."""
        role = Role.objects.create(
            name="admin",
            priority=80,
            permissions={"can_edit": True}
        )
        
        serializer = RoleSerializer(role)
        data = serializer.data
        
        assert data["name"] == "admin"
        assert data["permissions"] == {"can_edit": True}
        assert data["priority"] == 80

    def test_create_role(self):
        """Test role creation."""
        data = {
            "name": "viewer",
            "priority": 30,
            "permissions": {"can_view": True, "can_edit": False}
        }
        
        serializer = RoleSerializer(data=data)
        assert serializer.is_valid()
        
        role = serializer.save()
        assert role.name == "viewer"
        assert role.priority == 30


@pytest.mark.django_db
class TestMembershipSerializer:
    """Test cases for MembershipSerializer."""

    def setup_method(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )
        self.member_user = User.objects.create_user(
            email="member@example.com",
            username="memberuser",
            password="testpass123"
        )
        self.org = Organization.objects.create(
            name="Test Org",
            slug="test-org",
            created_by=self.user
        )
        self.role = Role.objects.create(
            name="member",
            priority=50
        )

    def test_serialize_membership(self):
        """Test membership serialization."""
        membership = Membership.objects.create(
            user=self.member_user,
            organization=self.org,
            role=self.role
        )
        
        serializer = MembershipSerializer(membership)
        data = serializer.data
        
        assert "user" in data
        assert "organization" in data
        assert "role" in data
        assert data["is_active"] is True


@pytest.mark.django_db
class TestMembershipCreateSerializer:
    """Test cases for MembershipCreateSerializer."""

    def setup_method(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123"
        )
        self.member_user = User.objects.create_user(
            email="member@example.com",
            username="memberuser",
            password="testpass123"
        )
        self.org = Organization.objects.create(
            name="Test Org",
            slug="test-org",
            created_by=self.user
        )
        self.role = Role.objects.create(
            name="member",
            priority=50
        )

    def test_create_membership_success(self):
        """Test successful membership creation."""
        data = {
            "user_email": "member@example.com",
            "role_name": "member",
            "organization": self.org.id
        }
        
        serializer = MembershipCreateSerializer(data=data)
        assert serializer.is_valid()
        
        membership = serializer.save()
        assert membership.user == self.member_user
        assert membership.organization == self.org
        assert membership.role == self.role

    def test_create_membership_invalid_email(self):
        """Test membership creation with invalid email."""
        data = {
            "user_email": "nonexistent@example.com",
            "role_name": "member",
            "organization": self.org.id
        }
        
        serializer = MembershipCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "user_email" in serializer.errors 