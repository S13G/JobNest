from typing import Dict

from django.contrib.auth import authenticate, get_user_model

from apps.core.models import EmployeeProfile, CompanyProfile

User = get_user_model()


def register_social_user(email: str, password: str, profile_model) -> Dict[str, str]:
    """
    Register a social user.

    Args:
        email: The email address of the user.
        password: The password of the user.
        profile_model: The profile model to create.

    Returns:
        A dictionary containing the user's email, full name, phone number, and tokens.
    """
    user_data = {
        "email": email,
        "password": password
    }
    user = User.objects.create_user(**user_data)
    profile_model.objects.create(user=user)
    user.email_verified = True
    user.google_provider = True
    user.save()

    authenticated_user = authenticate(email=email, password=password)
    return authenticated_user


def register_job_seeker_social_user(email: str, password: str) -> Dict[str, str]:
    return register_social_user(email, password, EmployeeProfile)


def register_job_recruiter_social_user(email: str, password: str) -> Dict[str, str]:
    return register_social_user(email, password, CompanyProfile)
