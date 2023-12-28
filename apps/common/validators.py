from django.core.exceptions import ValidationError


def validate_phone_number(value):
    if not value.startswith('+'):
        raise ValidationError("Phone number must start with country code e.g. (+44).", 400)
    elif not value[1:].isdigit():
        raise ValidationError("Phone number must be digits.", 400)
