import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


class CustomAccountManager(BaseUserManager):
    """
    Custom manager for the Account model.

    This manager uses email as the unique authentication identifier
    instead of usernames.
    """

    def create_user(
        self,
        email: str,
        first_name: str,
        last_name: str,
        username: str,
        phone_number: str | None = None,
        password: str | None = None,
        **extra_fields,
    ):
        """
        Create and return a regular user.

        Args:
            email (str): User email address.
            first_name (str): User first name.
            last_name (str): User last name.
            username (str): Unique username.
            phone_number (str | None): Optional phone number.
            password (str | None): Raw password.
            **extra_fields: Additional model fields.

        Returns:
            Account: Newly created user instance.

        Raises:
            ValueError: If required fields are missing.
        """

        if not email:
            raise ValueError("An email address is required.")

        if not username:
            raise ValueError("A username is required.")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            username=username,
            phone_number=phone_number,
            **extra_fields,
        )

        # Hash and store the password securely
        user.set_password(password)

        # Save user to the configured database
        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        email: str,
        first_name: str,
        last_name: str,
        username: str,
        password: str,
        **extra_fields,
    ):
        """
        Create and return a superuser.

        Args:
            email (str): Superuser email.
            first_name (str): First name.
            last_name (str): Last name.
            username (str): Unique username.
            password (str): Raw password.
            **extra_fields: Additional fields.

        Returns:
            Account: Newly created superuser instance.

        Raises:
            ValueError: If required admin flags are invalid.
        """

        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=password,
            **extra_fields,
        )



# User Roles
ROLE_CHOICES = (
    ("owner", "Owner"),
    ("senior_lawyer", "Senior Lawyer"),
    ("lawyer", "Lawyer"),
    ("assistant", "Assistant"),
    ("viewer", "Viewer"),
)


class Account(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for authentication and authorization.

    Uses email instead of username for authentication.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    email = models.EmailField(
        max_length=255,
        unique=True,
    )

    username = models.CharField(
        max_length=255,
        unique=True,
    )

    phone_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
    )

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default="viewer",
    )

    # Permission Flags
    is_active = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)

    last_login = models.DateTimeField(
        null=True,
        blank=True,
    )

    # Authentication Configuration
    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = [
        "username",
        "first_name",
        "last_name",
    ]

    # Attach custom manager
    objects = CustomAccountManager()

    class Meta:
        """
        Model metadata.
        """

        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        """
        Human-readable representation of the user.
        """
        return self.email

    @property
    def full_name(self) -> str:
        """
        Return the user's full name.
        """
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def get_short_name(self) -> str:
        """
        Return the user's short name.
        """
        return self.first_name

    def has_perm(self, perm, obj=None) -> bool:
        """
        Check if the user has a specific permission.

        Superusers automatically have all permissions.
        """
        return self.is_superuser

    def has_module_perms(self, app_label) -> bool:
        """
        Check if the user has permissions to view the app.
        """
        return True