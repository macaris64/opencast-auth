from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Organization(models.Model):
    """
    Organization model representing a tenant in the multi-tenant system.
    Each organization can have multiple users with different roles.
    """
    
    name = models.CharField(
        _("name"),
        max_length=255,
        help_text=_("Organization name")
    )
    
    slug = models.SlugField(
        _("slug"),
        max_length=255,
        unique=True,
        help_text=_("URL-friendly organization identifier")
    )
    
    description = models.TextField(
        _("description"),
        blank=True,
        help_text=_("Organization description")
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_organizations",
        help_text=_("User who created this organization")
    )
    
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_("Designates whether this organization is active")
    )
    
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    
    # Many-to-many relationship with User through Membership
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="Membership",
        related_name="organizations"
    )
    
    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organizations")
        ordering = ["name"]
    
    def __str__(self):
        return self.name
    
    @property
    def members_count(self):
        """Return the count of active members."""
        return self.memberships.filter(is_active=True).count()


class Role(models.Model):
    """
    Role model defining different roles within the system.
    Roles are global and can be used across all organizations.
    """
    
    ROLE_CHOICES = [
        ("owner", _("Owner")),
        ("admin", _("Admin")),
        ("member", _("Member")),
        ("viewer", _("Viewer")),
    ]
    
    name = models.CharField(
        _("name"),
        max_length=50,
        choices=ROLE_CHOICES,
        unique=True,
        help_text=_("Role name")
    )
    
    description = models.TextField(
        _("description"),
        blank=True,
        help_text=_("Role description")
    )
    
    priority = models.IntegerField(
        _("priority"),
        default=0,
        help_text=_("Role priority (higher number = higher priority)")
    )
    
    permissions = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("JSON object containing role permissions")
    )
    
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    
    class Meta:
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")
        ordering = ["-priority", "name"]
    
    def __str__(self):
        return self.get_name_display()


class Membership(models.Model):
    """
    Membership model representing the relationship between a User and an Organization.
    This is the through model for the many-to-many relationship.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships"
    )
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships"
    )
    
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="memberships",
        help_text=_("User's role in this organization")
    )
    
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_("Designates whether this membership is active")
    )
    
    joined_at = models.DateTimeField(_("joined at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    
    class Meta:
        verbose_name = _("Membership")
        verbose_name_plural = _("Memberships")
        unique_together = ["user", "organization"]
        ordering = ["organization", "user"]
    
    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role.get_name_display()})"
    
    def save(self, *args, **kwargs):
        """Save membership."""
        super().save(*args, **kwargs)
