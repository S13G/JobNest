from uuid import uuid4

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel
from apps.common.validators import validate_phone_number
from apps.core.managers import CustomUserManager


# Create your models here.


class User(AbstractBaseUser, BaseModel, PermissionsMixin):
    first_name = models.CharField(_("First name"), max_length=150, default='John')
    last_name = models.CharField(_("Last name"), max_length=150, default='Doe')
    email = models.EmailField(_("Email address"), unique=True)
    avatar = models.ImageField(upload_to="static/user_avatars", null=True, blank=True)
    phone_number = models.CharField(max_length=20, validators=[validate_phone_number])
    coins_available = models.PositiveIntegerField(default=0)
    email_verified = models.BooleanField(default=False)
    email_changed = models.BooleanField(default=False)
    email_modified_time = models.DateTimeField(default=None, null=True, editable=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone_number", "first_name", "last_name"]

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def profile_image(self):
        return self.avatar.url if self.avatar else ""


class OTPSecret(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="otp_secret", null=True)
    secret = models.CharField(max_length=255, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_profile")

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class AgentProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="agent_profile")
    date_of_birth = models.DateField(null=True)
    occupation = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
