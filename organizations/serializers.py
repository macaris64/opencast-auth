from rest_framework import serializers

from .models import Organization, Role, Membership
from accounts.serializers import UserSerializer


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model."""
    
    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "description",
            "priority",
            "permissions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MembershipSerializer(serializers.ModelSerializer):
    """Serializer for Membership model."""
    
    user = UserSerializer(read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    role_name = serializers.CharField(source="role.get_name_display", read_only=True)
    
    def to_representation(self, instance):
        """Customize serialization to include role details."""
        ret = super().to_representation(instance)
        ret['role'] = RoleSerializer(instance.role).data
        return ret
    
    class Meta:
        model = Membership
        fields = [
            "id",
            "user",
            "organization",
            "organization_name",
            "role",
            "role_name",
            "is_active",
            "joined_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "organization", "organization_name", "role_name", "joined_at", "updated_at"]


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model."""
    
    members_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "members_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def get_members_count(self, obj):
        """Return the number of active members."""
        return obj.memberships.filter(is_active=True).count()


class OrganizationDetailSerializer(OrganizationSerializer):
    """Detailed serializer for Organization model with members."""
    
    memberships = MembershipSerializer(many=True, read_only=True)
    
    class Meta(OrganizationSerializer.Meta):
        fields = OrganizationSerializer.Meta.fields + ["memberships"]


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating organizations."""
    
    class Meta:
        model = Organization
        fields = ["name", "slug", "description"]
    
    def create(self, validated_data):
        """Create organization and set creator as owner."""
        request = self.context.get("request")
        
        # Set created_by from request user
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        organization = Organization.objects.create(**validated_data)
        
        # Make the creator an owner with default owner role
        if request and request.user.is_authenticated:
            owner_role = Role.objects.get(name="owner")
            Membership.objects.create(
                user=request.user,
                organization=organization,
                role=owner_role
            )
        
        return organization


class MembershipCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating memberships."""
    
    user_email = serializers.EmailField(write_only=True)
    role_name = serializers.CharField(write_only=True)
    
    class Meta:
        model = Membership
        fields = ["user_email", "role_name", "organization"]
    
    def validate(self, attrs):
        """Validate membership creation."""
        from accounts.models import User
        
        user_email = attrs["user_email"]
        organization = attrs["organization"]
        role_name = attrs["role_name"]
        
        # Check if user exists
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"user_email": "User with this email does not exist."}
            )
        
        # Check if membership already exists
        if Membership.objects.filter(user=user, organization=organization).exists():
            raise serializers.ValidationError(
                "User is already a member of this organization."
            )
        
        # Get role
        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            raise serializers.ValidationError(
                {"role_name": "Role does not exist."}
            )
        
        attrs["user"] = user
        attrs["role"] = role
        return attrs
    
    def create(self, validated_data):
        """Create membership."""
        validated_data.pop("user_email")
        validated_data.pop("role_name")
        return Membership.objects.create(**validated_data) 