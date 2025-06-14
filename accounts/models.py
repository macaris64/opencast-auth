from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model that extends Django's AbstractUser.
    This model serves as the foundation for authentication in the system.
    """
    
    email = models.EmailField(
        _("email address"),
        unique=True,
        help_text=_("Required. A valid email address.")
    )
    
    first_name = models.CharField(
        _("first name"),
        max_length=150,
        blank=True
    )
    
    last_name = models.CharField(
        _("last name"),
        max_length=150,
        blank=True
    )
    
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    
    date_joined = models.DateTimeField(_("date joined"), auto_now_add=True)
    
    # Override username field to use email
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
    
    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        db_table = "auth_user"
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_organizations(self):
        """Get all organizations this user belongs to."""
        return self.memberships.select_related("organization").values_list(
            "organization", flat=True
        )
