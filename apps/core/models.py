from uuid import uuid4

import pycountry
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.models import BaseModel
from apps.core.managers import CustomUserManager


# Create your models here.


class User(AbstractBaseUser, BaseModel, PermissionsMixin):
    email = models.EmailField(_("Email address"), unique=True)
    avatar = models.ImageField(upload_to="static/user_avatars", null=True, blank=True)
    company = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    google_provider = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    USERNAME_FIELD = "email"

    objects = CustomUserManager()

    # Generate JWT tokens for the user(using this specifically for oauth)
    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }

    def __str__(self):
        return self.email

    @property
    def profile_image_url(self):
        return self.avatar.url if self.avatar else ""


class OTPSecret(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="otp_secret", null=True)
    secret = models.CharField(max_length=255, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.email


class EmployeeProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employee_profile")
    full_name = models.CharField(_("Full name"), max_length=255)
    date_of_birth = models.DateField(null=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    occupation = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} > {self.full_name}"


class CompanyProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="company_profile")
    name = models.CharField(_("Company name"), max_length=255)
    country = models.CharField(
        max_length=255, null=True, choices=[(country.alpha_2, country.name) for country in pycountry.countries]
    )
    address = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} > {self.name}"
