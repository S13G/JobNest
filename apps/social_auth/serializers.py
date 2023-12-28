import secrets

from django.contrib.auth import get_user_model
from faker import Faker
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.core.serializers import EmployeeProfileSerializer, CompanyProfileSerializer
from apps.social_auth import google
# from apps.core.serializers import ProfileSerializer
from apps.social_auth.funcs import register_social_user

fake = Faker()

User = get_user_model()


class GoogleSocialAuthSerializer(serializers.Serializer):
    auth_token = serializers.CharField()

    def validate_auth_token(self, auth_token):
        user_data = self._validate_google_auth_token(auth_token)
        email = user_data.get('email')
        password = secrets.token_hex(8)

        try:
            user = self._get_existing_user(email)
        except User.DoesNotExist:
            user = register_social_user(email=email, password=password)
        return self._get_user_data(user)

    @staticmethod
    def _validate_google_auth_token(auth_token):
        user_data = google.Google.validate(auth_token)
        if 'sub' not in user_data:
            raise ValidationError("The token is invalid or expired, please login again.")

        if user_data['iss'] != 'https://accounts.google.com':
            raise ValidationError("Invalid Issuer. Google didn't issue this.")
        return user_data

    @staticmethod
    def _get_existing_user(email):
        user = User.objects.get(email=email)
        return user

    @staticmethod
    def _get_user_data(user):
        # Checking the type of profile it is (employee or company) and sending it to frontend
        if hasattr(User, 'employee_profile'):
            profile = user.employee_profile
            profile_serializer = EmployeeProfileSerializer(profile)
        else:
            profile = user.company_profile
            profile_serializer = CompanyProfileSerializer(profile)

        return {
            "tokens": user.tokens(),
            "data": {
                "user_id": user.id,
                "profile": profile_serializer.data,
            }
        }
