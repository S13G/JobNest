# import secrets
import secrets

from django.contrib.auth import get_user_model
from faker import Faker
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.core.serializers import EmployeeProfileSerializer, CompanyProfileSerializer
from apps.social_auth import google
from apps.social_auth.funcs import register_job_seeker_social_user, register_job_recruiter_social_user

fake = Faker()

User = get_user_model()


class BaseGoogleSocialAuthSerializer(serializers.Serializer):
    """
    Validates an ID token and returns user data.

    Args:
        id_token (str): The ID token to validate.
        register_func (function): The function to use for user registration.
        profile_serializer (object): The serializer to use for user profile data.

    Returns:
        dict: The user data.

    Raises:
        User.DoesNotExist: If the user does not exist in the database.
    """
    id_token = serializers.CharField()

    def validate_id_token(self, id_token, register_func, profile_serializer):
        """
        Validates an ID token and performs necessary actions based on the token's validity.

        Parameters:
            id_token (str): The ID token to be validated.
            register_func (function): A function that registers a new user.
            profile_serializer (Serializer): A serializer for user profile data.

        Returns:
            dict: The user data associated with the validated ID token.
        """
        user_data = self._validate_google_id_token(id_token)
        email = user_data.get('email')
        password = secrets.token_hex(8)

        try:
            user = self._get_existing_user(email)
        except User.DoesNotExist:
            user = register_func(email=email, password=password)

        return self._get_user_data(user, profile_serializer)

    @staticmethod
    def _validate_google_id_token(id_token):
        user_data = google.Google.validate(id_token)

        # Check if the 'sub' key is present in the user data
        if 'sub' not in user_data:
            raise ValidationError("The token is invalid or expired, please login again.")

        # Check if the issuer is valid
        if user_data['iss'] != 'https://accounts.google.com':
            raise ValidationError("Invalid Issuer. Google didn't issue this.")

        # Return the user data
        return user_data

    @staticmethod
    def _get_existing_user(email):
        user = User.objects.get(email=email)
        return user

    @staticmethod
    def _get_user_data(user, profile_serializer_cls):
        """
        Get user data for serialization.

        Args:
            user (User): The user object containing user data.
            profile_serializer_cls (Serializer): The serializer class for serializing the user profile.

        Returns:
            dict: A dictionary containing the user data.

        """
        # Determine the profile type based on whether the user has a company profile or an employee profile
        profile_type = "company_profile" if user.company_profile else "employee_profile"

        # Check if the user already has a profile of the same type
        try:
            profile = getattr(user, profile_type)
            profile_serializer = profile_serializer_cls(profile)
            profile_data = profile_serializer.data
            user_data = {
                "tokens": user.tokens(),
                "data": {
                    "user_id": user.id,
                    "profile": profile_data,
                }
            }
            return user_data
        except AttributeError:
            raise RequestError(err_code=ErrorCode.ALREADY_EXISTS, err_msg=f"User already has a {profile_type}.",
                               status_code=status.HTTP_409_CONFLICT)


class JobSeekerGoogleSocialAuthSerializer(BaseGoogleSocialAuthSerializer):
    def validate_id_token(self, id_token):
        return super().validate_id_token(
            id_token,
            register_job_seeker_social_user,
            EmployeeProfileSerializer,
        )


class JobRecruiterGoogleSocialAuthSerializer(BaseGoogleSocialAuthSerializer):
    def validate_id_token(self, id_token):
        return super().validate_id_token(
            id_token,
            register_job_recruiter_social_user,
            CompanyProfileSerializer,
        )
