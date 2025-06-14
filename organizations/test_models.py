import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from organizations.models import Organization, Role, Membership

User = get_user_model()


class OrganizationModelTests(TestCase):
    """Test cases for Organization model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        
        # Create default roles
        self.owner_role = Role.objects.create(
            name="owner",
            description="Organization owner",
            priority=100
        )
    
    def test_organization_creation(self):
        """Test organization creation with valid data."""
        org = Organization.objects.create(
            name="Test Organization",
            slug="test-org",
            description="Test Description",
            created_by=self.user,
        )
        
        assert org.name == "Test Organization"
        assert org.slug == "test-org" 
        assert org.description == "Test Description"
        assert org.created_by == self.user
        assert org.is_active == True
        assert str(org) == "Test Organization"
    
    def test_organization_slug_uniqueness(self):
        """Test that organization slugs must be unique."""
        Organization.objects.create(
            name="Test Organization 1",
            slug="test-org",
            created_by=self.user,
        )
        
        with pytest.raises(Exception):  # IntegrityError
            Organization.objects.create(
                name="Test Organization 2", 
                slug="test-org",
                created_by=self.user,
            )
    
    def test_organization_members_count(self):
        """Test members count calculation."""
        org = Organization.objects.create(
            name="Test Organization",
            slug="test-org",
            created_by=self.user,
        )
        
        # Initially 0 members
        assert org.members_count == 0
        
        # Add membership
        Membership.objects.create(
            user=self.user,
            organization=org,
            role=self.owner_role,
        )
        
        # Refresh from database
        org.refresh_from_db()
        assert org.members_count == 1


class RoleModelTests(TestCase):
    """Test cases for Role model."""
    
    def setUp(self):
        """Set up test data."""
        # Create test roles
        Role.objects.create(name="owner", priority=100)
        Role.objects.create(name="admin", priority=80)
        Role.objects.create(name="member", priority=50)
        Role.objects.create(name="viewer", priority=10)
    
    def test_default_roles_created(self):
        """Test that default roles are created."""
        expected_roles = ["owner", "admin", "member", "viewer"]
        
        for role_name in expected_roles:
            role = Role.objects.get(name=role_name)
            assert role.name == role_name
            assert str(role) == role_name.title()
    
    def test_role_ordering(self):
        """Test role ordering by priority."""
        roles = list(Role.objects.all())
        
        # Should be ordered by priority (higher priority first)
        assert roles[0].name == "owner"
        assert roles[1].name == "admin"  
        assert roles[2].name == "member"
        assert roles[3].name == "viewer"


class MembershipModelTests(TestCase):
    """Test cases for Membership model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com", 
            password="testpass123",
        )
        
        self.org = Organization.objects.create(
            name="Test Organization",
            slug="test-org",
            created_by=self.user,
        )
        
        # Create test role
        self.role = Role.objects.create(
            name="member",
            description="Regular member",
            priority=50
        )
    
    def test_membership_creation(self):
        """Test membership creation with valid data."""
        membership = Membership.objects.create(
            user=self.user,
            organization=self.org,
            role=self.role,
        )
        
        assert membership.user == self.user
        assert membership.organization == self.org
        assert membership.role == self.role
        assert membership.is_active == True
        assert str(membership) == f"{self.user.email} - {self.org.name} ({self.role.get_name_display()})"
    
    def test_membership_uniqueness(self):
        """Test that user can only have one membership per organization."""
        Membership.objects.create(
            user=self.user,
            organization=self.org,
            role=self.role,
        )
        
        with pytest.raises(Exception):  # IntegrityError
            Membership.objects.create(
                user=self.user,
                organization=self.org,
                role=self.role,
            )
    
    def test_membership_user_organizations_relationship(self):
        """Test that membership creates proper user-organization relationship."""
        membership = Membership.objects.create(
            user=self.user,
            organization=self.org,
            role=self.role,
        )
        
        # User should be in organization
        assert self.org in self.user.organizations.all()
        
        # Organization should have user as member
        assert self.user in self.org.members.all() 