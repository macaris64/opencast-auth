from django.shortcuts import render
from django.db import models
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Organization, Membership
from .serializers import (
    OrganizationSerializer,
    OrganizationDetailSerializer,
    OrganizationCreateSerializer,
    MembershipSerializer,
    MembershipCreateSerializer,
)


@extend_schema_view(
    list=extend_schema(
        operation_id="organizations_list",
        summary="List organizations",
        description="Get a list of organizations the user has access to.",
    ),
    retrieve=extend_schema(
        operation_id="organizations_retrieve",
        summary="Get organization details",
        description="Get detailed information about a specific organization.",
    ),
    create=extend_schema(
        operation_id="organizations_create",
        summary="Create organization",
        description="Create a new organization.",
    ),
    update=extend_schema(
        operation_id="organizations_update",
        summary="Update organization",
        description="Update organization information.",
    ),
    partial_update=extend_schema(
        operation_id="organizations_partial_update",
        summary="Partial update organization",
        description="Partially update organization information.",
    ),
)
class OrganizationViewSet(ModelViewSet):
    """ViewSet for Organization model."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter organizations based on user permissions."""
        user = self.request.user
        
        if user.is_staff:
            return Organization.objects.all()
        
        # Return organizations where user is a member
        return Organization.objects.filter(
            memberships__user=user,
            memberships__is_active=True,
            is_active=True
        ).distinct()
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == "create":
            return OrganizationCreateSerializer
        elif self.action == "retrieve":
            return OrganizationDetailSerializer
        return OrganizationSerializer
    
    def perform_update(self, serializer):
        """Update organization with permission check."""
        organization = self.get_object()
        
        # Check if user has permission to update
        user_membership = organization.memberships.filter(
            user=self.request.user, is_active=True
        ).first()
        
        if not user_membership or user_membership.role.name not in ["owner", "admin"]:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to update this organization.")
        
        serializer.save()
    
    @extend_schema(
        operation_id="organizations_members",
        summary="List organization members",
        description="Get list of members in the organization.",
        responses={200: MembershipSerializer(many=True)},
    )
    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        """Get organization members."""
        organization = self.get_object()
        memberships = organization.memberships.filter(is_active=True).select_related(
            "user", "role"
        )
        serializer = MembershipSerializer(memberships, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        operation_id="organizations_add_member",
        summary="Add member to organization",
        description="Add a new member to the organization.",
        request=MembershipCreateSerializer,
        responses={201: MembershipSerializer},
    )
    @action(detail=True, methods=["post"])
    def add_member(self, request, pk=None):
        """Add member to organization."""
        organization = self.get_object()
        
        # Check if user has permission to add members
        user_membership = organization.memberships.filter(
            user=request.user, is_active=True
        ).first()
        
        if not user_membership or user_membership.role.name not in ["owner", "admin"]:
            return Response(
                {"error": "You don't have permission to add members to this organization."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MembershipCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Set organization from URL parameter
            serializer.validated_data["organization"] = organization
            membership = serializer.save()
            
            return Response(
                MembershipSerializer(membership).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        operation_id="organizations_remove_member",
        summary="Remove member from organization",
        description="Remove a member from the organization.",
        responses={204: None},
    )
    @action(detail=True, methods=["delete"], url_path="members/(?P<user_id>[^/.]+)")
    def remove_member(self, request, pk=None, user_id=None):
        """Remove member from organization."""
        organization = self.get_object()
        
        # Check if user has permission to remove members
        user_membership = organization.memberships.filter(
            user=request.user, is_active=True
        ).first()
        
        if not user_membership or user_membership.role.name not in ["owner", "admin"]:
            return Response(
                {"error": "You don't have permission to remove members from this organization."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            membership = organization.memberships.get(user__id=user_id, is_active=True)
            
            # Prevent removing the last owner
            if membership.role.name == "owner":
                owner_count = organization.memberships.filter(
                    role__name="owner", is_active=True
                ).count()
                if owner_count <= 1:
                    return Response(
                        {"error": "Cannot remove the last owner of the organization."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            membership.is_active = False
            membership.save()
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except Membership.DoesNotExist:
            return Response(
                {"error": "User is not a member of this organization."},
                status=status.HTTP_404_NOT_FOUND
            )


@extend_schema_view(
    list=extend_schema(
        operation_id="memberships_list",
        summary="List memberships",
        description="Get a list of user's memberships.",
    ),
    retrieve=extend_schema(
        operation_id="memberships_retrieve",
        summary="Get membership details",
        description="Get details of a specific membership.",
    ),
)
class MembershipViewSet(ModelViewSet):
    """ViewSet for Membership model."""
    
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch", "options", "head"]  # Read-only mostly
    
    def get_queryset(self):
        """Filter memberships based on user permissions."""
        user = self.request.user
        queryset = Membership.objects.select_related("organization", "role", "user")
        
        if user.is_staff:
            return queryset
        
        # For detail view, allow access to memberships in organizations where user is owner/admin
        if self.action in ['retrieve', 'update', 'partial_update']:
            user_managed_orgs = Organization.objects.filter(
                memberships__user=user,
                memberships__is_active=True,
                memberships__role__name__in=['owner', 'admin'],
                is_active=True
            ).values_list('id', flat=True)
            
            # Return memberships in organizations where user is owner/admin OR user's own memberships
            return queryset.filter(
                models.Q(organization_id__in=user_managed_orgs) | 
                models.Q(user=user),
                is_active=True
            )
        
        # Filter by organization if provided
        organization_id = self.request.query_params.get('organization')
        if organization_id:
            # Check if user is member of the organization
            user_orgs = Organization.objects.filter(
                memberships__user=user,
                memberships__is_active=True,
                is_active=True
            ).values_list('id', flat=True)
            
            if int(organization_id) in user_orgs:
                return queryset.filter(
                    organization_id=organization_id,
                    is_active=True
                )
            else:
                return queryset.none()
        
        # Return user's own memberships
        return queryset.filter(user=user, is_active=True)
    
    def perform_update(self, serializer):
        """Update membership with permission check."""
        membership = self.get_object()
        
        # Check if user has permission to update membership roles
        user_membership = membership.organization.memberships.filter(
            user=self.request.user, is_active=True
        ).first()
        
        if not user_membership or user_membership.role.name not in ["owner", "admin"]:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to update membership roles.")
        
        serializer.save()
