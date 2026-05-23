from django.db import models
from django.contrib.auth.models import AbtractBaseUser, PermissionsMixin, BaseUserManager
import uuid
from django.utils import timezone


class CustomAccountManager(BaseUserManager):
    
    """
    Custom manager for Account model where email is the unique identifier
    """
    
    def create_user(self,
                    email,
                    ):
        pass


ROLE_CHOICES = (
        ("owner", "Owner"),
        ("senior_lawyer", "Senior Lawyer"),
        ("lawyer", "Lawyer"),
        ("assistant", "Assistant"),
        ("viewer", "Viewer"),
    )


# Account model for database
class Account(AbtractBaseUser):
    id = UUIDField(
        primary_key = True,
        default = uuid.uuid4,
        editable = False
    )
    # fields
    first_name = models.CharField(max_length = 100)
    last_name = models.CharField(max_length = 100)
    
    email = models.EmailField(max_length=255, unique=True)
    
    username = models.CharField(max_length=255, unique=True)
    
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
    )
    
    # system flags
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    
    date_joined = models.DateTimeField(default=timezone.now())
    last_login = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    
    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        odering = ['-date_joined']
        
        
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_short_name(self):
        return f"{self.first_name}"
    
    def has_perm(self, perm, obj = None):
        return is_admin
    
    der has_module_perms(self, app_label):
        reutrn True
    
    