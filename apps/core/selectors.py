from django.contrib.auth import get_user_model
from rest_framework import status

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.core.emails import decode_otp_from_secret
from apps.core.models import EmployeeProfile, CompanyProfile
from apps.notification.choices import NOTIFICATION_COMPLETE_PROFILE
from apps.notification.models import Notification

User = get_user_model()


def validate_profile_existence(email: str) -> None:
    user = User.objects.get_or_none(email=email)

    if user:
        profile = 'employee' if hasattr(user, 'employee_profile') else 'company'
        raise RequestError(
            err_code=ErrorCode.ALREADY_EXISTS,
            err_msg=f"Account already exists and has {profile} profile",
            status_code=status.HTTP_409_CONFLICT
        )


def create_employee_profile(email: str, data: dict) -> None or (EmployeeProfile, User):
    validate_profile_existence(email)

    try:
        user = User.objects.create_user(**data)
        employee_instance = EmployeeProfile.objects.create(user=user)

    except Exception as e:
        raise RequestError(err_code=ErrorCode.OTHER_ERROR, err_msg=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    Notification.objects.create(user=user, notification_type=NOTIFICATION_COMPLETE_PROFILE,
                                message="Complete your profile")
    return employee_instance, user


def create_company_profile(email: str, data: dict) -> None or (CompanyProfile, User):
    validate_profile_existence(email)

    try:
        user = User.objects.create_user(**data, company=True)
        company_instance = CompanyProfile.objects.create(user=user)

    except Exception as e:
        raise RequestError(err_code=ErrorCode.OTHER_ERROR, err_msg=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    Notification.objects.create(user=user, notification_type=NOTIFICATION_COMPLETE_PROFILE,
                                message="Complete your profile")
    return company_instance, user


def get_existing_user(email: str) -> None or User:
    user = User.objects.get_or_none(email=email)
    if user is None:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="User with this email not found",
                           status_code=status.HTTP_404_NOT_FOUND)

    return user


def check_existing_user(email: str) -> None:
    user = User.objects.get_or_none(email=email)
    if user is not None:
        raise RequestError(err_code=ErrorCode.ALREADY_EXISTS, err_msg="User with this email exists",
                           status_code=status.HTTP_409_CONFLICT)


def otp_verification(otp_secret: str, code: str):
    otp = decode_otp_from_secret(otp_secret=otp_secret)

    if otp != code:
        raise RequestError(err_code=ErrorCode.INCORRECT_OTP, err_msg="Invalid OTP",
                           status_code=status.HTTP_400_BAD_REQUEST)


def get_employee_profile(user: User) -> EmployeeProfile:
    try:
        return EmployeeProfile.objects.select_related('user').get(user=user)
    except EmployeeProfile.DoesNotExist:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No profile found for this user",
                           status_code=status.HTTP_404_NOT_FOUND)


def get_company_profile(user: User) -> CompanyProfile:
    try:
        return CompanyProfile.objects.select_related('user').get(user=user)
    except CompanyProfile.DoesNotExist:
        raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No profile found for this user",
                           status_code=status.HTTP_404_NOT_FOUND)
