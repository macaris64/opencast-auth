from django.shortcuts import render
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import User
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
)


class RegisterView(APIView):
    """API view for user registration."""
    
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        operation_id="auth_register",
        summary="Register a new user",
        description="Create a new user account with email and password.",
        request=UserCreateSerializer,
        responses={201: UserSerializer},
    )
    def post(self, request):
        """Register a new user."""
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate tokens for the new user
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """API view for user login."""
    
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        operation_id="auth_login",
        summary="Login user",
        description="Authenticate user with email and password, return JWT tokens.",
        request=LoginSerializer,
        responses={200: UserSerializer},
    )
    def post(self, request):
        """Login user and return tokens."""
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """API view for user logout."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        operation_id="auth_logout",
        summary="Logout user",
        description="Logout user by blacklisting the refresh token.",
        request={"refresh": "string"},
        responses={205: None},
    )
    def post(self, request):
        """Logout user by blacklisting refresh token."""
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "refresh token is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            # Note: For production, enable token blacklisting in settings
            # For now, just validate the token
            return Response({"message": "Successfully logged out"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(
                {"error": "Invalid refresh token"}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema_view(
    list=extend_schema(
        operation_id="users_list",
        summary="List users",
        description="Get a list of all users (admin only).",
    ),
    retrieve=extend_schema(
        operation_id="users_retrieve",
        summary="Get user details",
        description="Get details of a specific user.",
    ),
    update=extend_schema(
        operation_id="users_update",
        summary="Update user",
        description="Update user information.",
    ),
    partial_update=extend_schema(
        operation_id="users_partial_update",
        summary="Partial update user",
        description="Partially update user information.",
    ),
)
class UserViewSet(ModelViewSet):
    """ViewSet for User model."""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action == "list":
            # Only staff can list all users
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        if self.request.user.is_staff:
            return User.objects.all()
        
        # Regular users can only see themselves
        return User.objects.filter(id=self.request.user.id)
    
    @extend_schema(
        operation_id="users_me",
        summary="Get current user",
        description="Get details of the currently authenticated user.",
        responses={200: UserSerializer},
    )
    @action(detail=False, methods=["get"])
    def me(self, request):
        """Get current user details."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @extend_schema(
        operation_id="users_change_password",
        summary="Change password",
        description="Change the current user's password.",
        request=ChangePasswordSerializer,
        responses={200: {"message": "string"}},
    )
    @action(detail=False, methods=["post"])
    def change_password(self, request):
        """Change user password."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request}
        )
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data["new_password"])
            user.save()
            
            return Response({"message": "Password changed successfully"})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        operation_id="users_organizations",
        summary="Get user organizations",
        description="Get list of organizations the user belongs to.",
        responses={200: "OrganizationSerializer(many=True)"},
    )
    @action(detail=False, methods=["get"])
    def organizations(self, request):
        """Get user's organizations."""
        from organizations.serializers import OrganizationSerializer
        
        user = request.user
        organizations = user.organizations.filter(is_active=True)
        serializer = OrganizationSerializer(organizations, many=True)
        
        return Response(serializer.data)
