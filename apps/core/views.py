from datetime import timedelta

import pyotp
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer, \
    TokenRefreshSerializer, TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenBlacklistView, TokenRefreshView

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.permissions import IsAuthenticatedEmployee, IsAuthenticatedCompany
from apps.common.responses import CustomResponse
from apps.core.emails import send_otp_email
from apps.core.models import OTPSecret, EmployeeProfile, CompanyProfile
from apps.core.serializers import *
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
                description="Account already exists and has Employee profile",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Bad request",
            )
        }
    )
    @transaction.atomic()
    def post(self, request):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')

        if User.objects.filter(email=email).exists():
            if hasattr(User.objects.get(email=email), 'employee'):
                profile = 'Employee'
            else:
                profile = 'Company'

            raise RequestError(err_code=ErrorCode.ALREADY_EXISTS,
                               err_msg=f"Account already exists and has ${profile} profile",
                               status_code=status.HTTP_409_CONFLICT)

        try:
            user = User.objects.create_user(**serializer.validated_data)
            employee_instance = EmployeeProfile.objects.create(user=user)
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
                description="Account already exists and has Company profile",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Bad request",
            )
        }
    )
    @transaction.atomic()
    def post(self, request):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')

        if User.objects.filter(email=email).exists():
            if hasattr(User.objects.get(email=email), 'employee'):
                profile = 'Employee'
            else:
                profile = 'Company'

            raise RequestError(err_code=ErrorCode.ALREADY_EXISTS,
                               err_msg=f"Account already exists and has ${profile} profile",
                               status_code=status.HTTP_409_CONFLICT)

        try:
            user = User.objects.create_user(**serializer.validated_data)
            company_instance = CompanyProfile.objects.create(user=user)
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
                description="Email verification successful or already verified.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="OTP Error"
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="User with this email not found or otp not found for user"
            )
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')
        code = self.request.data.get('otp')

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
                description="Verification code sent successfully. Please check your mail. or Email verified already.",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="User with this email not found"
            )
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=self.request.data)
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
                description="Verification code sent successfully. Please check your new email.",
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                description="Account with this email already exists"
            )
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        existing_user = User.objects.filter(email=email).exists()

        if existing_user:
            raise RequestError(err_code=ErrorCode.ALREADY_EXISTS, err_msg="Account with this email already exists",
                               status_code=status.HTTP_409_CONFLICT)
        else:
            send_otp_email(self.request.user, template="email_change.html")
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
                description="Email changed successfully.",
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                description="You can't use your previous email"
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="OTP Error"
            ),
        }
    )
    @transaction.atomic()
    def post(self, request):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        new_email = serializer.validated_data.get('email')
        code = self.request.data.get('code')
        user = self.request.user

        if user.email == new_email:
            raise RequestError(err_code=ErrorCode.OLD_EMAIL, err_msg="You can't use your previous email", )
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
    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        summary="Login",
        description="""
        This endpoint authenticates a registered and verified user and provides the necessary authentication tokens.
        """,
        request=LoginSerializer,
        tags=['Authentication'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Logged in successfully",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Account not active or Invalid credentials",
            ),
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        email = validated_data["email"]
        password = validated_data["password"]

        user = authenticate(request, email=email, password=password)

        if not user:
            raise RequestError(err_code=ErrorCode.INVALID_CREDENTIALS, err_msg="Invalid credentials",
                               status_code=status.HTTP_400_BAD_REQUEST)

        if not user.email_verified:
            raise RequestError(err_code=ErrorCode.UNVERIFIED_USER, err_msg="Verify your email first",
                               status_code=status.HTTP_400_BAD_REQUEST)

        # Checking the type of profile it is (employee or company) and sending it to frontend
        if hasattr(User, 'employee_profile'):
            profile = user.employee_profile
            profile_serializer = EmployeeProfileSerializer(profile)
        else:
            profile = user.company_profile
            profile_serializer = CompanyProfileSerializer(profile)

        # tokens
        tokens_response = super().post(request)
        tokens = {"refresh": tokens_response['refresh'], "access": tokens_response['access']}

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
                description="Token is blacklisted",
            ),
            status.HTTP_200_OK: OpenApiResponse(
                description="Logged out successfully"
            )
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=self.request.data)
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
                description="Account not found"
            ),
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                description="Password code sent successfully"
            )
        }

    )
    def post(self, request):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        email = self.request.data.get('email')

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
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="OTP error"
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Account not found"
            ),
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                description="Otp verified successfully"
            )
        }

    )
    def post(self, request):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        email = self.request.data.get("email")
        code = self.request.data.get("otp")

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
            status.HTTP_200_OK: OpenApiResponse(
                description="Password updated successfully",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Token not provided"
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
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        password = serializer.validated_data['password']
        user.set_password(password)
        user.save()

        return CustomResponse.success(message="Password updated successfully")


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
            status.HTTP_200_OK: OpenApiResponse(
                description="Password updated successfully",
            ),
        }
    )
    @transaction.atomic()
    def post(self, request):
        user = self.request.user
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        password = serializer.validated_data['password']
        user.set_password(password)
        user.save()

        return CustomResponse.success(message="Password updated successfully")


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
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Provide a profile id"
            ),
            status.HTTP_200_OK: OpenApiResponse(
                description="Fetched successfully",
                response=EmployeeProfileSerializer
            )
        }
    )
    def get(self, request):
        user = self.request.user

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
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Provide a profile id"
            ),
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                description="Updated successfully",
                response=EmployeeProfileSerializer
            )
        }
    )
    @transaction.atomic()
    def patch(self, request):
        user = self.request.user

        profile_instance = EmployeeProfile.objects.select_related('user').get(user=user)

        update_profile = self.serializer_class(profile_instance, data=self.request.data, partial=True)
        update_profile.is_valid(raise_exception=True)

        updated = self.serializer_class(update_profile.save()).data
        return CustomResponse.success(message="Updated profile successfully", data=updated,
                                      status_code=status.HTTP_202_ACCEPTED)

    @extend_schema(
        summary="Delete employee profile",
        description=
        """
        This endpoint allows a user to delete his/her employee profile.
        """,
        tags=['Employee Profile'],
        responses={
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Provide a profile id"
            ),
            status.HTTP_200_OK: OpenApiResponse(
                description="Deleted successfully"
            )
        }
    )
    def delete(self, request):
        user = self.request.user
        EmployeeProfile.objects.select_related('user').get(user=user).delete()
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
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Provide a profile id"
            ),
            status.HTTP_200_OK: OpenApiResponse(
                description="Fetched successfully",
                response=CompanyProfileSerializer
            )
        }
    )
    def get(self, request):
        user = self.request.user

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
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Provide a profile id"
            ),
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                description="Updated successfully",
                response=CompanyProfileSerializer
            )
        }
    )
    @transaction.atomic()
    def patch(self, request):
        user = self.request.user

        profile_instance = CompanyProfile.objects.select_related('user').get(user=user)

        update_profile = self.serializer_class(profile_instance, data=self.request.data, partial=True)
        update_profile.is_valid(raise_exception=True)
        updated = self.serializer_class(update_profile.save()).data

        return CustomResponse.success(message="Updated profile successfully", data=updated,
                                      status_code=status.HTTP_202_ACCEPTED)

    @extend_schema(
        summary="Delete company profile",
        description=
        """
        This endpoint allows a user to delete his/her company profile.
        """,
        tags=['Company Profile'],
        responses={
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Provide a profile id"
            ),
            status.HTTP_200_OK: OpenApiResponse(
                description="Deleted successfully"
            )
        }
    )
    def delete(self, request):
        user = self.request.user
        CompanyProfile.objects.select_related('user').get(user=user).delete()
        return CustomResponse.success(message="Deleted successfully")
