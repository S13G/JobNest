import pycountry
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from rest_framework import serializers as sr

User = get_user_model()


class RegisterSerializer(sr.Serializer):
    email = sr.CharField()
    password = sr.CharField(write_only=True)


class VerifyEmailSerializer(sr.Serializer):
    email = sr.CharField()
    otp = sr.IntegerField()

    @staticmethod
    def validate_email(value):
        try:
            validate_email(value)
        except sr.ValidationError:
            raise sr.ValidationError("Invalid email address.")
        return value


class ResendEmailVerificationCodeSerializer(sr.Serializer):
    email = sr.CharField()

    @staticmethod
    def validate_email(value):
        try:
            validate_email(value)
        except sr.ValidationError:
            raise sr.ValidationError("Invalid email address.")
        return value


class SendNewEmailVerificationCodeSerializer(sr.Serializer):
    email = sr.CharField()

    @staticmethod
    def validate_email(value):
        try:
            validate_email(value)
        except sr.ValidationError:
            raise sr.ValidationError("Invalid email address.")
        return value


class ChangeEmailSerializer(sr.Serializer):
    email = sr.CharField()
    otp = sr.IntegerField()

    @staticmethod
    def validate_email(value):
        try:
            validate_email(value)
        except sr.ValidationError:
            raise sr.ValidationError("Invalid email address.")
        return value


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
        return instance


class CompanyProfileSerializer(sr.Serializer):
    user = sr.HiddenField(default=sr.CurrentUserDefault())
    user_id = sr.UUIDField(read_only=True)
    id = sr.UUIDField(read_only=True)
    name = sr.CharField()
    country = sr.ChoiceField(choices=[(country.alpha_2, country.name) for country in pycountry.countries])
    email = sr.EmailField(source="user.email", read_only=True)
    avatar = sr.ImageField(source="user.avatar")
    address = sr.CharField()

    def to_representation(self, instance):
        data = super().to_representation(instance)
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
        return instance


class LoginSerializer(sr.Serializer):
    email = sr.CharField()
    password = sr.CharField(write_only=True)

    @staticmethod
    def validate_email(value):
        try:
            validate_email(value)
        except sr.ValidationError:
            raise sr.ValidationError("Invalid email address.")
        return value


class ChangePasswordSerializer(sr.Serializer):
    password = sr.CharField(max_length=50, min_length=6, write_only=True)
    confirm_pass = sr.CharField(max_length=50, min_length=6, write_only=True)

    def validate(self, attrs):
        password = attrs.get('password')
        confirm = attrs.get('confirm_pass')

        if confirm != password:
            raise sr.ValidationError({"confirm_pass": "Passwords do not match"})
        return attrs


class RequestNewPasswordCodeSerializer(sr.Serializer):
    email = sr.CharField()

    @staticmethod
    def validate_email(value):
        try:
            validate_email(value)
        except sr.ValidationError:
            raise sr.ValidationError("Invalid email address.")
        return value
