from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from rest_framework import serializers as sr
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.common.validators import validate_phone_number

User = get_user_model()


class RegisterSerializer(sr.Serializer):
    first_name = sr.CharField(default="John")
    last_name = sr.CharField(default="Doe")
    email = sr.CharField()
    phone_number = sr.CharField(validators=[validate_phone_number])
    password = sr.CharField(write_only=True)

    @staticmethod
    def validate_email(value):
        try:
            validate_email(value)
        except sr.ValidationError:
            raise sr.ValidationError("Invalid email address.")
        return value


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


class ProfileSerializer(sr.Serializer):
    user_id = sr.UUIDField(read_only=True, source="user.id")
    id = sr.UUIDField(read_only=True)
    first_name = sr.CharField(source="user.first_name")
    last_name = sr.CharField(source="user.last_name")
    email = sr.EmailField(source="user.email", read_only=True)
    avatar = sr.ImageField(source="user.avatar")
    coins_available = sr.IntegerField(source="user.coins_available", read_only=True)
    phone_number = sr.CharField(validators=[validate_phone_number], source="user.phone_number")

    def to_representation(self, instance):
        data = super().to_representation(instance)

        for field_name, field_value in data.items():
            if field_value is None:
                data[field_name] = ""

        return data

    def update(self, instance, validated_data):
        user = instance.user
        first_name = validated_data.get('first_name')
        last_name = validated_data.get('last_name')
        phone_number = validated_data.get('phone_number')

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


class AgentProfileSerializer(sr.Serializer):
    user_id = sr.UUIDField(read_only=True, source="user.id")
    id = sr.UUIDField(read_only=True)
    first_name = sr.CharField(source="user.first_name")
    last_name = sr.CharField(source="user.last_name")
    avatar = sr.ImageField(source="user.avatar")
    email = sr.EmailField(source="user.email", read_only=True)
    coins_available = sr.IntegerField(source="user.coins_available", read_only=True)
    date_of_birth = sr.DateField()
    phone_number = sr.CharField(validators=[validate_phone_number], source="user.phone_number")
    occupation = sr.CharField()
    address = sr.CharField()

    def to_representation(self, instance):
        data = super().to_representation(instance)

        for field_name, field_value in data.items():
            if field_value is None:
                data[field_name] = ""

        return data

    def update(self, instance, validated_data):
        user = instance.user
        first_name = validated_data.get('first_name')
        last_name = validated_data.get('last_name')
        phone_number = validated_data.get('phone_number')

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
