import pyotp
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

from utilities.emails import send_email

User = get_user_model()


def decode_otp_from_secret(otp_secret: str) -> str:
    # Generate the OTP using the secret
    # Otp lasts for 5 minutes
    totp = pyotp.TOTP(s=otp_secret, interval=300, digits=4)  # Limit the generated otp to 4 digits

    otp = totp.now()
    return otp


def send_otp_email(otp_secret: str, recipient: str or User, template=None) -> None:
    # Generate the OTP using the secret
    otp = decode_otp_from_secret(otp_secret=otp_secret)

    # Determine email address based on the type of recipient
    if isinstance(recipient, User):
        email_address = recipient.email
    else:
        email_address = recipient

    subject = 'One-Time Password (OTP) Verification'
    recipients = [email_address]
    context = {'email': email_address, 'otp': otp}
    message = render_to_string(template, context)

    # Send the email
    send_email(subject, recipients, message=message, template=template, context=context)
