from datetime import timedelta

import pyotp
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema, OpenApiExample
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer, TokenRefreshSerializer, \
    TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenBlacklistView, TokenRefreshView

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.permissions import IsAuthenticatedEmployee, IsAuthenticatedCompany
from apps.common.responses import CustomResponse
from apps.core.emails import send_otp_email
from apps.core.models import OTPSecret, EmployeeProfile, CompanyProfile
from apps.core.serializers import *
from apps.notification.choices import NOTIFICATION_COMPLETE_PROFILE, NOTIFICATION_PROFILE_UPDATED
from apps.notification.models import Notification
from utilities.encryption import decrypt_token_to_profile, encrypt_profile_to_token

User = get_user_model()

# Create your views here.


"""
REGISTRATION
"""


class EmployeeRegistrationView(APIView):
    serializer_class = RegisterSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Employee registration",
        description=(
                """
                This endpoint allows a user to register an employee account.
                The request should include the following data:
                - `email`: The email address.
                - `password`: The password.
                """
        ),
        tags=['Registration'],
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Registration successful, check your email for verification.",
                response=EmployeeProfileSerializer
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                response={"status": "failure", "message": "Account already exists and has Employee or Company profile",
                          "code": "already_exists"},
                description="Account already exists and has Employee or Company profile",
                examples=[
                    OpenApiExample(
                        name="Conflict response",
                        value={
                            "status": "failure",
                            "message": "Account already exists and has Employee or Company profile",
                            "code": "already_exists"
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Bad request",
            )
        }
    )
    @transaction.atomic()
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            if hasattr(user, 'employee_profile'):
                profile = 'employee'
            else:
                profile = 'company'

            raise RequestError(err_code=ErrorCode.ALREADY_EXISTS,
                               err_msg=f"Account already exists and has {profile} profile",
                               status_code=status.HTTP_409_CONFLICT)

        try:
            user = User.objects.create_user(**serializer.validated_data, is_active=True, company=True)
            employee_instance = EmployeeProfile.objects.create(user=user)
            Notification.objects.create(user=user, notification_type=NOTIFICATION_COMPLETE_PROFILE,
                                        message="Complete your profile")
        except Exception as e:
            raise RequestError(err_code=ErrorCode.OTHER_ERROR, err_msg=str(e), status_code=status.HTTP_400_BAD_REQUEST)

        data = EmployeeProfileSerializer(employee_instance).data

        send_otp_email(user=user, template='email_verification.html')
        return CustomResponse.success(message="Registration successful, check your email for verification.",
                                      status_code=status.HTTP_201_CREATED, data=data)


class CompanyRegistrationView(APIView):
    serializer_class = RegisterSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Company registration",
        description=(
                """
                This endpoint allows a user to register a company account.
                The request should include the following data:
                - `email`: The email address.
                - `password`: The password.
                """
        ),
        tags=['Registration'],
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Registration successful, check your email for verification.",
                response=CompanyProfileSerializer
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                response={"status": "failure", "message": "Account already exists and has Employee or Company profile",
                          "code": "already_exists"},
                description="Account already exists and has Employee or Company profile",
                examples=[
                    OpenApiExample(
                        name="Conflict response",
                        value={
                            "status": "failure",
                            "message": "Account already exists and has Employee or Company profile",
                            "code": "already_exists"
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Bad request",
            )
        }
    )
    @transaction.atomic()
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')

        if User.objects.filter(email=email).exists():
            if hasattr(User.objects.get(email=email), 'employee_profile'):
                profile = 'employee'
            else:
                profile = 'company'

            raise RequestError(err_code=ErrorCode.ALREADY_EXISTS,
                               err_msg=f"Account already exists and has {profile} profile",
                               status_code=status.HTTP_409_CONFLICT)

        try:
            user = User.objects.create_user(**serializer.validated_data, is_active=True, company=True)
            company_instance = CompanyProfile.objects.create(user=user)
            Notification.objects.create(user=user, notification_type=NOTIFICATION_COMPLETE_PROFILE,
                                        message="Complete your profile")
        except Exception as e:
            raise RequestError(err_code=ErrorCode.OTHER_ERROR, err_msg=str(e), status_code=status.HTTP_400_BAD_REQUEST)

        data = CompanyProfileSerializer(company_instance).data

        send_otp_email(user=user, template='email_verification.html')
        return CustomResponse.success(message="Registration successful, check your email for verification.",
                                      status_code=status.HTTP_201_CREATED, data=data)


"""
AUTHENTICATION AND VERIFICATION OPTIONS 
"""


class VerifyEmailView(APIView):
    serializer_class = VerifyEmailSerializer

    @extend_schema(
        summary="Email verification",
        description=
        """
        This endpoint allows a registered user to verify their email address with an OTP.
        The request should include the following data:

        - `email_address`: The user's email address.
        - `otp`: The otp sent to the user's email address.
        """,
        tags=['Email Verification'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"status": "success", "message": "Email verification successful or already verified."},
                description="Email verification successful or already verified.",
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Email verification successful"
                        }
                    ),
                    OpenApiExample(
                        name="Already verified response",
                        value={
                            "status": "error",
                            "message": "Email already verified",
                            "code": "verified_user"
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={"status": "failure", "message": "Invalid OTP", "code": "incorrect_otp"},
                description="OTP Error",
                examples=[
                    OpenApiExample(
                        name="Invalid OTP response",
                        value={
                            "status": "failure",
                            "message": "Invalid OTP",
                            "code": "incorrect_otp"
                        }
                    ),
                    OpenApiExample(
                        name="Expired OTP response",
                        value={
                            "status": "failure",
                            "message": "OTP has expired",
                            "code": "expired_otp"
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"status": "failure", "message": "Not found", "code": "non_existent"},
                description="Not found",
                examples=[
                    OpenApiExample(
                        name="Email not found response",
                        value={
                            "status": "failure",
                            "message": "User with this email not found",
                            "code": "non_existent"
                        }
                    ),
                    OpenApiExample(
                        name="No otp found response",
                        value={
                            "status": "failure",
                            "message": "No OTP found for this account",
                            "code": "non_existent"
                        }
                    ),
                    OpenApiExample(
                        name="No OTP secret found response",
                        value={
                            "status": "failure",
                            "message": "No OTP secret found for this account",
                            "code": "non_existent"
                        }
                    )
                ]
            )
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')
        code = request.data.get('otp')

        try:
            user = User.objects.select_related('otp_secret').get(email=email)
        except User.DoesNotExist:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="User with this email not found",
                               status_code=status.HTTP_404_NOT_FOUND)

        if user.email_verified:
            raise RequestError(err_code=ErrorCode.VERIFIED_USER, err_msg="Email verified already",
                               status_code=status.HTTP_200_OK)
        try:
            if not code or not user.otp_secret:
                raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No OTP found for this account",
                                   status_code=status.HTTP_404_NOT_FOUND)

            # Verify the OTP
            totp = pyotp.TOTP(user.otp_secret.secret, interval=600)
            if not totp.verify(code):
                raise RequestError(err_code=ErrorCode.INCORRECT_OTP, err_msg="Invalid OTP",
                                   status_code=status.HTTP_400_BAD_REQUEST)

            # Check if the OTP secret has expired (10 minutes interval)
            current_time = timezone.now()
            expiration_time = user.otp_secret.created + timedelta(minutes=10)
            if current_time > expiration_time:
                raise RequestError(err_code=ErrorCode.EXPIRED_OTP, err_msg="OTP has expired",
                                   status_code=status.HTTP_400_BAD_REQUEST)
        except OTPSecret.DoesNotExist:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No OTP secret found for this account",
                               status_code=status.HTTP_404_NOT_FOUND)

        # OTP verification successful
        user.email_verified = True
        user.save()
        user.otp_secret.delete()

        return CustomResponse.success(message="Email verification successful.")


class ResendEmailVerificationCodeView(APIView):
    serializer_class = ResendEmailVerificationCodeSerializer

    @extend_schema(
        summary="Send / resend email verification code",
        description=
        """
        This endpoint allows a registered user to send or resend email verification code to their registered email address.
        The request should include the following data:

        - `email_address`: The user's email address.
        """,
        tags=['Email Verification'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"status": "success",
                          "message": "Verification code sent successfully. Please check your mail."},
                description="Verification code sent successfully. Please check your mail.",
                examples=[
                    OpenApiExample(
                        name="Verification successful response",
                        value={
                            "status": "success",
                            "message": "Verification code sent successfully. Please check your mail."
                        }
                    ),
                    OpenApiExample(
                        name="Already verified response",
                        value={
                            "status": "error",
                            "message": "Email already verified",
                            "error_code": "already_verified"
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"status": "failure", "message": "User with this email not found", "code": "non_existent"},
                description="User with this email not found",
                examples=[
                    OpenApiExample(
                        name="Email not found response",
                        value={
                            "status": "failure",
                            "message": "User with this email not found",
                            "code": "non_existent"
                        }
                    )
                ]
            )
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="User with this email not found",
                               status_code=status.HTTP_404_NOT_FOUND)

        if user.email_verified:
            raise RequestError(err_code=ErrorCode.VERIFIED_USER, err_msg="Email already verified",
                               status_code=status.HTTP_200_OK)

        send_otp_email(user, template="email_verification.html")
        return CustomResponse.success("Verification code sent successfully. Please check your mail")


class SendNewEmailVerificationCodeView(APIView):
    serializer_class = SendNewEmailVerificationCodeSerializer

    @extend_schema(
        summary="Send email change verification code",
        description=
        """
        This endpoint allows an authenticated user to send a verification code to new email they want to change to.
        The request should include the following data:

        - `email_address`: The user's new email address.
        """,
        tags=['Email Change'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"status": "success",
                          "message": "Verification code sent successfully. Please check your new email."},
                description="Verification code sent successfully. Please check your new email.",
                examples=[
                    OpenApiExample(
                        name="Verification successful response",
                        value={
                            "status": "success",
                            "message": "Verification code sent successfully. Please check your new email."
                        }
                    )
                ]
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                response={"status": "failure", "message": "Account with this email already exists",
                          "code": "already_exists"},
                description="Account with this email already exists",
                examples=[
                    OpenApiExample(
                        name="Conflict response",
                        value={
                            "status": "failure",
                            "message": "Account with this email already exists",
                            "code": "already_exists"
                        }
                    )
                ]
            )
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        existing_user = User.objects.filter(email=email).exists()

        if existing_user:
            raise RequestError(err_code=ErrorCode.ALREADY_EXISTS, err_msg="Account with this email already exists",
                               status_code=status.HTTP_409_CONFLICT)
        else:
            send_otp_email(request.user, template="email_change.html")
        return CustomResponse.success("Verification code sent successfully. Please check your mail")


class ChangeEmailView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangeEmailSerializer

    @extend_schema(
        summary="Change account email address",
        description=
        """
        This endpoint allows an authenticated user to change their account's email address and user can change after 10 days.
        The request should include the following data:

        - `email_address`: The user's new email address.
        - `otp`: The code sent
        """,
        tags=['Email Change'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"status": "success", "message": "Email changed successfully."},
                description="Email changed successfully.",
                examples=[
                    OpenApiExample(
                        name="Successful response",
                        value={
                            "status": "success",
                            "message": "Email changed successfully."
                        }
                    )
                ]
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                response={"status": "failure", "message": "You can't use your previous email", "code": "old_email"},
                description="You can't use your previous email",
                examples=[
                    OpenApiExample(
                        name="Old email response",
                        value={
                            "status": "failure",
                            "message": "You can't use your previous email",
                            "code": "old_email"
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={"status": "failure", "message": "Invalid OTP", "code": "incorrect_otp"},
                description="OTP Error",
                examples=[
                    OpenApiExample(
                        name="Invalid OTP response",
                        value={
                            "status": "failure",
                            "message": "Invalid OTP",
                            "code": "incorrect_otp"
                        }
                    ),
                    OpenApiExample(
                        name="Expired OTP response",
                        value={
                            "status": "failure",
                            "message": "OTP has expired",
                            "code": "expired_otp"
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"status": "failure", "message": "Not found", "code": "non_existent"},
                description="Not OTP found",
                examples=[
                    OpenApiExample(
                        name="No otp found response",
                        value={
                            "status": "failure",
                            "message": "No OTP found for this account",
                            "code": "non_existent"
                        }
                    ),

                ]
            )
        }
    )
    @transaction.atomic()
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_email = serializer.validated_data.get('email')
        code = request.data.get('code')
        user = request.user

        if user.email == new_email:
            raise RequestError(err_code=ErrorCode.OLD_EMAIL, err_msg="You can't use your previous email",
                               status_code=status.HTTP_403_FORBIDDEN)
        elif not code or not user.otp_secret:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No OTP found for this account",
                               status_code=status.HTTP_404_NOT_FOUND)

        # Check if the OTP secret has expired (10 minutes interval)
        current_time = timezone.now()
        expiration_time = user.otp_secret.created + timedelta(minutes=10)
        if current_time > expiration_time:
            raise RequestError(err_code=ErrorCode.EXPIRED_OTP, err_msg="OTP has expired",
                               status_code=status.HTTP_400_BAD_REQUEST)

        # Verify the OTP
        totp = pyotp.TOTP(user.otp_secret.secret, interval=600)
        if not totp.verify(code):
            raise RequestError(err_code=ErrorCode.INCORRECT_OTP, err_msg="Invalid OTP",
                               status_code=status.HTTP_400_BAD_REQUEST)

        user.email = new_email
        user.save()
        user.otp_secret.delete()

        return CustomResponse.success(message="Email changed successfully.")


class LoginView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Login",
        description="""
        This endpoint authenticates a registered and verified user and provides the necessary authentication tokens.
        """,
        request=LoginSerializer,
        tags=['Login'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=LoginSerializer,
                description="Logged in successfully",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={"status": "failure", "message": "Invalid credentials", "code": "invalid_credentials"},
                description="Invalid credentials",
                examples=[
                    OpenApiExample(
                        name="Invalid credentials",
                        value={
                            "status": "failure",
                            "message": "Invalid credentials",
                            "code": "invalid_credentials"
                        }
                    ),
                    OpenApiExample(
                        name="Unverified email response",
                        value={
                            "status": "failure",
                            "message": "Verify your email first",
                            "code": "unverified_email"
                        }
                    )
                ]
            ),
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        # authenticating user
        user = authenticate(request, email=email, password=password)

        if not user or not user.check_password(password):
            raise RequestError(err_code=ErrorCode.INVALID_CREDENTIALS, err_msg="Invalid credentials",
                               status_code=status.HTTP_400_BAD_REQUEST)

        if not user.email_verified:
            raise RequestError(err_code=ErrorCode.UNVERIFIED_USER, err_msg="Verify your email first",
                               status_code=status.HTTP_400_BAD_REQUEST)

        # Checking the type of profile it is (employee or company) and sending it to frontend
        if hasattr(user, 'employee_profile'):
            profile = user.employee_profile
            profile_serializer = EmployeeProfileSerializer(profile)
        else:
            profile = user.company_profile
            profile_serializer = CompanyProfileSerializer(profile)

        # tokens
        tokens_response = super().post(request)
        tokens = {"refresh": tokens_response.data['refresh'], "access": tokens_response.data['access']}

        response_data = {"tokens": tokens, "profile_data": profile_serializer.data}
        return CustomResponse.success(message="Logged in successfully", data=response_data)


class LogoutView(TokenBlacklistView):
    serializer_class = TokenBlacklistSerializer

    @extend_schema(
        summary="Logout",
        description=
        """
        This endpoint logs out an authenticated user by blacklisting their access token.
        The request should include the following data:

        - `refresh`: The refresh token used for authentication.
        """,
        tags=['Logout'],
        responses={
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={"status": "failure", "message": "Token is blacklisted", "code": "invalid_entry"},
                description="Token is blacklisted",
                examples=[
                    OpenApiExample(
                        name="Blacklisted token response",
                        value={
                            "status": "failure",
                            "message": "Token is blacklisted",
                            "code": "invalid_entry"
                        }
                    )
                ]
            ),
            status.HTTP_200_OK: OpenApiResponse(
                response={"status": "success", "message": "Logged out successfully"},
                description="Logged out successfully",
                examples=[
                    OpenApiExample(
                        name="Logout successful response",
                        value={
                            "status": "success",
                            "message": "Logged out successfully"
                        }
                    )
                ]
            )
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return CustomResponse.success(message="Logged out successfully.")
        except TokenError:
            raise RequestError(err_code=ErrorCode.INVALID_ENTRY, err_msg="Token is blacklisted",
                               status_code=status.HTTP_400_BAD_REQUEST)


class RefreshView(TokenRefreshView):
    serializer_class = TokenRefreshSerializer

    @extend_schema(
        summary="Refresh token",
        description=
        """
        This endpoint allows a user to refresh an expired access token.
        The request should include the following data:

        - `refresh`: The refresh token.
        """,
        tags=['Token'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=TokenRefreshSerializer,
                description="Refreshed successfully",
            ),
        }

    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        access_token = serializer.validated_data['access']
        return CustomResponse.success(message="Refreshed successfully", data=access_token)


class RequestForgotPasswordCodeView(APIView):
    serializer_class = RequestNewPasswordCodeSerializer
    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        summary="Request new password code for forgot password",
        description=
        """
        This endpoint allows a user to request a verification code to reset their password if forgotten.
        The request should include the following data:

        - `email`: The user's email address.
        """,
        tags=['Password Change'],
        responses={
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"status": "failure", "message": "Account not found", "code": "non_existent"},
                description="Account not found",
                examples=[
                    OpenApiExample(
                        name="Account not found response",
                        value={
                            "status": "failure",
                            "message": "Account not found",
                            "code": "non_existent"
                        }
                    )
                ]
            ),
            status.HTTP_200_OK: OpenApiResponse(
                response={"status": "success", "message": "Password code sent successfully"},
                description="Password code sent successfully",
                examples=[
                    OpenApiExample(
                        name="Password code sent response",
                        value={
                            "status": "success",
                            "message": "Password code sent successfully"
                        }
                    )
                ]
            )
        }

    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = request.data.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Account not found",
                               status_code=status.HTTP_404_NOT_FOUND)

        send_otp_email(user, "forgot_password.html")
        return CustomResponse.success(message="Password code sent successfully")


class VerifyForgotPasswordCodeView(APIView):
    serializer_class = VerifyEmailSerializer
    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        summary="Verify forgot password code for unauthenticated users",
        description=
        """
        This endpoint allows a user to verify the verification code they got to reset the password if forgotten.
        The user will be stored in the token which will be gotten to make sure it is the right user that is
        changing his/her password

        The request should include the following data:

        - `email`: The user's email
        - `otp`: The verification code sent to the user's email.
        """,
        tags=['Password Change'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"status": "success", "message": "Otp verified successfully."},
                description="Otp verified successfully.",
                examples=[
                    OpenApiExample(
                        name="Otp verified response",
                        value={
                            "status": "success",
                            "message": "Otp verified successfully",
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={"status": "failure", "message": "Invalid OTP", "code": "incorrect_otp"},
                description="OTP Error",
                examples=[
                    OpenApiExample(
                        name="Invalid OTP response",
                        value={
                            "status": "failure",
                            "message": "Invalid OTP",
                            "code": "incorrect_otp"
                        }
                    ),
                    OpenApiExample(
                        name="Expired OTP response",
                        value={
                            "status": "failure",
                            "message": "OTP has expired",
                            "code": "expired_otp"
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"status": "failure", "message": "Not found", "code": "non_existent"},
                description="Not found",
                examples=[
                    OpenApiExample(
                        name="Email not found response",
                        value={
                            "status": "failure",
                            "message": "User with this email not found",
                            "code": "non_existent"
                        }
                    ),
                    OpenApiExample(
                        name="No otp found response",
                        value={
                            "status": "failure",
                            "message": "No OTP found for this account",
                            "code": "non_existent"
                        }
                    ),
                    OpenApiExample(
                        name="No OTP secret found response",
                        value={
                            "status": "failure",
                            "message": "No OTP secret found for this account",
                            "code": "non_existent"
                        }
                    )
                ]
            )
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = request.data.get("email")
        code = request.data.get("otp")

        try:
            user = User.objects.select_related('otp_secret').get(email=email)
        except User.DoesNotExist:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="User with this email not found",
                               status_code=status.HTTP_404_NOT_FOUND)

        try:
            if not code or not user.otp_secret:
                raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No OTP found for this account",
                                   status_code=status.HTTP_404_NOT_FOUND)

            # Verify the OTP
            totp = pyotp.TOTP(user.otp_secret.secret, interval=600)
            if not totp.verify(code):
                raise RequestError(err_code=ErrorCode.INCORRECT_OTP, err_msg="Invalid OTP",
                                   status_code=status.HTTP_400_BAD_REQUEST)

            # Check if the OTP secret has expired (10 minutes interval)
            current_time = timezone.now()
            expiration_time = user.otp_secret.created + timedelta(minutes=10)
            if current_time > expiration_time:
                raise RequestError(err_code=ErrorCode.EXPIRED_OTP, err_msg="OTP has expired",
                                   status_code=status.HTTP_400_BAD_REQUEST)

        except OTPSecret.DoesNotExist:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No OTP secret found for this account",
                               status_code=status.HTTP_404_NOT_FOUND)

        token = encrypt_profile_to_token(user)  # Encrypt the user profile to a token.
        return CustomResponse.success(message="Otp verified successfully", data=token)


class ChangeForgottenPasswordView(APIView):
    serializer_class = ChangePasswordSerializer
    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        summary="Change password for forgotten password",
        description=
        """
        This endpoint allows the unauthenticated user to change their password after requesting for a code.
        The request should include the following data:

        - `password`: The new password.
        - `confirm_password`: The new password again.
        """,
        tags=['Password Change'],
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                response={"status": "success", "message": "Password updated successfully."},
                description="Password updated successfully",
                examples=[
                    OpenApiExample(
                        name="Password updated response",
                        value={
                            "status": "success",
                            "message": "Password updated successfully.",
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={"status": "failure", "message": "Token not provided", "code": "invalid_entry"},
                description="Token not provided",
                examples=[
                    OpenApiExample(
                        name="Token not provided response",
                        value={
                            "status": "failure",
                            "message": "Token not provided",
                            "code": "invalid_entry"
                        }
                    )
                ]
            )
        }
    )
    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        token = self.kwargs.get('token')
        if token is None:
            raise RequestError(err_code=ErrorCode.INVALID_ENTRY, err_msg="Token not provided",
                               status_code=status.HTTP_404_NOT_FOUND)

        user = decrypt_token_to_profile(token)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        password = serializer.validated_data['password']
        user.set_password(password)
        user.save()

        return CustomResponse.success(message="Password updated successfully", status_code=status.HTTP_202_ACCEPTED)


class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        summary="Change password for authenticated users",
        description=
        """
        This endpoint allows the authenticated user to change their password.
        The request should include the following data:

        - `password`: The new password.
        - `confirm_password`: The new password again.
        """,
        tags=['Password Change'],
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                response={"status": "success", "message": "Password updated successfully"},
                description="Password updated successfully",
                examples=[
                    OpenApiExample(
                        name="Password updated response",
                        value={
                            "status": "success",
                            "message": "Password updated successfully",
                        }
                    )
                ]
            ),
        }
    )
    @transaction.atomic()
    def post(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        password = serializer.validated_data['password']
        user.set_password(password)
        user.save()

        return CustomResponse.success(message="Password updated successfully", status_code=status.HTTP_202_ACCEPTED)


"""
EMPLOYEE PROFILE
"""


class RetrieveUpdateDeleteEmployeeProfileView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)
    serializer_class = EmployeeProfileSerializer

    @extend_schema(
        summary="Retrieve employee profile",
        description=
        """
        This endpoint allows a user to retrieve his/her employee profile.
        """,
        tags=['Employee Profile'],
        responses={
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"status": "failure", "message": "No profile found for this user", "code": "non_existent"},
                description="No profile found for this user",
                examples=[
                    OpenApiExample(
                        name="No profile found response",
                        value={
                            "status": "failure",
                            "message": "No profile found for this user",
                            "code": "non_existent"
                        }
                    )
                ]
            ),
            status.HTTP_200_OK: OpenApiResponse(
                description="Retrieved profile successfully",
                response=EmployeeProfileSerializer
            )
        }
    )
    def get(self, request):
        user = request.user

        try:
            profile_instance = EmployeeProfile.objects.select_related('user').get(user=user)
        except EmployeeProfile.DoesNotExist:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No profile found for this user",
                               status_code=status.HTTP_404_NOT_FOUND)

        serialized_data = self.serializer_class(profile_instance, context={"request": request}).data
        return CustomResponse.success(message="Retrieved profile successfully", data=serialized_data)

    @extend_schema(
        summary="Update employee profile",
        description=
        """
        This endpoint allows a user to update his/her employee profile.
        """,
        tags=['Employee Profile'],
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                description="Updated profile successfully",
                response=EmployeeProfileSerializer
            )
        }
    )
    @transaction.atomic()
    def patch(self, request):
        user = request.user

        profile_instance = EmployeeProfile.objects.select_related('user').get(user=user)

        update_profile = self.serializer_class(profile_instance, data=request.data, partial=True)
        update_profile.is_valid(raise_exception=True)
        updated = self.serializer_class(update_profile.save()).data

        Notification.objects.create(user=user, notification_type=NOTIFICATION_PROFILE_UPDATED,
                                    message="Profile updated successfully")

        return CustomResponse.success(message="Updated profile successfully", data=updated,
                                      status_code=status.HTTP_202_ACCEPTED)

    @extend_schema(
        summary="Delete employee account",
        description=
        """
        This endpoint allows a user to delete his/her employee account.
        """,
        tags=['Employee Profile'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"status": "success", "message": "Deleted successfully"},
                description="Deleted successfully",
                examples=[
                    OpenApiExample(
                        name="Deleted response",
                        value={
                            "status": "success",
                            "message": "Deleted successfully"
                        }
                    )
                ]
            )
        }
    )
    def delete(self, request):
        user = request.user
        user.delete()
        return CustomResponse.success(message="Deleted successfully")


"""
COMPANY PROFILE
"""


class RetrieveUpdateDeleteCompanyProfileView(APIView):
    permission_classes = (IsAuthenticatedCompany,)
    serializer_class = CompanyProfileSerializer

    @extend_schema(
        summary="Retrieve company profile",
        description=
        """
        This endpoint allows a user to retrieve his/her company profile.
        """,
        tags=['Company Profile'],
        responses={
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"status": "failure", "message": "No profile found for this user", "code": "non_existent"},
                description="No profile found for this user",
                examples=[
                    OpenApiExample(
                        name="No profile found response",
                        value={
                            "status": "failure",
                            "message": "No profile found for this user",
                            "code": "non_existent"
                        }
                    )
                ]
            ),
            status.HTTP_200_OK: OpenApiResponse(
                description="Retrieved profile successfully",
                response=CompanyProfileSerializer
            )
        }
    )
    def get(self, request):
        user = request.user

        try:
            profile_instance = CompanyProfile.objects.select_related('user').get(user=user)
        except CompanyProfile.DoesNotExist:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No profile found for this user",
                               status_code=status.HTTP_404_NOT_FOUND)

        serialized_data = self.serializer_class(profile_instance, context={"request": request}).data
        return CustomResponse.success(message="Retrieved profile successfully", data=serialized_data)

    @extend_schema(
        summary="Update company profile",
        description=
        """
        This endpoint allows a user to update his/her company profile.
        """,
        tags=['Company Profile'],
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                description="Updated profile successfully",
                response=CompanyProfileSerializer
            )
        }
    )
    @transaction.atomic()
    def patch(self, request):
        user = request.user

        profile_instance = CompanyProfile.objects.select_related('user').get(user=user)

        update_profile = self.serializer_class(profile_instance, data=request.data, partial=True)
        update_profile.is_valid(raise_exception=True)
        updated = self.serializer_class(update_profile.save()).data

        Notification.objects.create(user=user, notification_type=NOTIFICATION_PROFILE_UPDATED,
                                    message="Profile updated successfully")

        return CustomResponse.success(message="Updated profile successfully", data=updated,
                                      status_code=status.HTTP_202_ACCEPTED)

    @extend_schema(
        summary="Delete company account",
        description=
        """
        This endpoint allows a user to delete his/her account.
        """,
        tags=['Company Profile'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"status": "success", "message": "Deleted successfully"},
                description="Deleted successfully",
                examples=[
                    OpenApiExample(
                        name="Deleted response",
                        value={
                            "status": "success",
                            "message": "Deleted successfully"
                        }
                    )
                ]
            )
        }
    )
    def delete(self, request):
        user = request.user
        user.delete()
        return CustomResponse.success(message="Deleted successfully")
