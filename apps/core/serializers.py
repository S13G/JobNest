import pycountry
from django.contrib.auth import get_user_model
from django.core import validators
from django.core.validators import validate_email
from rest_framework import serializers as sr

from utilities.cache_clear import clear_user_cache

User = get_user_model()


def validate_email_address(value: str) -> str:
    """
        Validates an email address.
        Parameters:
            value (str): The email address to be validated.
        Returns:
            str: The validated email address
    """

    try:
        validate_email(value)
    except sr.ValidationError:
        raise sr.ValidationError("Invalid email address.")
    return value


class RegisterSerializer(sr.Serializer):
    email = sr.CharField()
    password = sr.CharField(max_length=20, write_only=True, min_length=8, validators=[validators.RegexValidator(
        regex=r'[!@#$%^&*(),.?":{}|<>]',
        message="Password must contain at least one special character."
    )], default="Validpass#1234")


class VerifyEmailSerializer(sr.Serializer):
    email = sr.CharField(validators=[validate_email_address])
    otp = sr.CharField()


class ResendEmailVerificationCodeSerializer(sr.Serializer):
    email = sr.CharField(validators=[validate_email_address])


class SendNewEmailVerificationCodeSerializer(sr.Serializer):
    email = sr.CharField(validators=[validate_email_address])


class ChangeEmailSerializer(sr.Serializer):
    email = sr.CharField(validators=[validate_email_address])
    otp = sr.CharField()


class EmployeeProfileSerializer(sr.Serializer):
    user = sr.HiddenField(default=sr.CurrentUserDefault())
    user_id = sr.UUIDField(read_only=True)
    id = sr.UUIDField(read_only=True)
    full_name = sr.CharField()
    date_of_birth = sr.DateField()
    email = sr.EmailField(source="user.email", read_only=True)
    address = sr.CharField()
    occupation = sr.CharField()
    avatar = sr.ImageField(source="user.avatar")

    def to_representation(self, instance):
        data = super().to_representation(instance)

        for field_name, field_value in data.items():
            if field_value is None:
                data[field_name] = ""

        return data

    def update(self, instance, validated_data):
        user = instance.user

        for key, value in validated_data.items():
            if key != 'user':  # Exclude the 'user' field
                setattr(instance, key, value)

        # Handle the 'user' field separately
        user_data = validated_data.get('user')
        if user_data:
            for key, value in user_data.items():
                setattr(instance.user, key, value)

        user.save()
        instance.save()

        # Clear cache data
        clear_user_cache(user_id=user.id, pattern_string="employee_profile")
        return instance


class CompanyProfileSerializer(sr.Serializer):
    user = sr.HiddenField(default=sr.CurrentUserDefault())
    user_id = sr.UUIDField(read_only=True)
    id = sr.UUIDField(read_only=True)
    name = sr.CharField()
    country = sr.ChoiceField(choices=[(country.alpha_2, country.name) for country in pycountry.countries], default='US')
    email = sr.EmailField(source="user.email", read_only=True)
    avatar = sr.ImageField(source="user.avatar")
    address = sr.CharField()

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if data['country'] is not None:
            data['country'] = pycountry.countries.get(alpha_2=data['country']).name

        for field_name, field_value in data.items():
            if field_value is None:
                data[field_name] = ""

        return data

    def update(self, instance, validated_data):
        user = instance.user

        for key, value in validated_data.items():
            if key != 'user':  # Exclude the 'user' field
                setattr(instance, key, value)

        # Handle the 'user' field separately
        user_data = validated_data.get('user')
        if user_data:
            for key, value in user_data.items():
                setattr(instance.user, key, value)

        user.save()
        instance.save()

        # Clear cache data
        clear_user_cache(user_id=user.id, pattern_string="company_profile")
        return instance


class LoginSerializer(sr.Serializer):
    email = sr.CharField(validators=[validate_email_address])
    password = sr.CharField(write_only=True)


class ChangePasswordSerializer(sr.Serializer):
    password = sr.CharField(max_length=20, min_length=8, write_only=True, validators=[validators.RegexValidator(
        regex=r'[!@#$%^&*(),.?":{}|<>]',
        message="Password must contain at least one special character."
    )], default="Validpass#1234")


class RequestNewPasswordCodeSerializer(sr.Serializer):
    email = sr.CharField(validators=[validate_email_address])
