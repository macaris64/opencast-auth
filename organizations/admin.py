from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Organization, Role, Membership


class MembershipInline(admin.TabularInline):
    """Inline admin for Membership model."""
    model = Membership
    extra = 0
    fields = ["user", "role", "is_active", "joined_at"]
    readonly_fields = ["joined_at"]


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin interface for Organization model."""
    
    list_display = ["name", "slug", "created_by", "is_active", "created_at", "members_count"]
    list_filter = ["is_active", "created_at", "created_by"]
    search_fields = ["name", "slug", "description", "created_by__email"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = (
        (None, {"fields": ("name", "slug", "description", "created_by", "is_active")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )
    
    inlines = [MembershipInline]
    
    def members_count(self, obj):
        """Return the number of active members in the organization."""
        return obj.members_count
    members_count.short_description = _("Active Members")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin interface for Role model."""
    
    list_display = ["name", "priority", "created_at", "members_count"] 
    list_filter = ["name", "priority", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = (
        (None, {"fields": ("name", "description", "priority", "permissions")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )
    
    def members_count(self, obj):
        """Return the number of users with this role."""
        return obj.memberships.filter(is_active=True).count()
    members_count.short_description = _("Active Members")


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    """Admin interface for Membership model."""
    
    list_display = ["user", "organization", "role", "is_active", "joined_at"]
    list_filter = ["is_active", "role__name", "organization", "joined_at"]
    search_fields = ["user__email", "user__username", "organization__name"]
    readonly_fields = ["joined_at", "updated_at"]
    
    fieldsets = (
        (None, {"fields": ("user", "organization", "role", "is_active")}),
        (_("Timestamps"), {"fields": ("joined_at", "updated_at")}),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            "user", "organization", "role"
        )
