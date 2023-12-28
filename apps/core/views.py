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
    TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenBlacklistView, TokenRefreshView

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.permissions import IsAuthenticatedAgent, IsAuthenticatedUser
from apps.common.responses import CustomResponse
from apps.core.emails import send_otp_email
from apps.core.models import OTPSecret, Profile, AgentProfile
from apps.core.serializers import *
from utilities.encryption import decrypt_token_to_profile, encrypt_profile_to_token

User = get_user_model()

# Create your views here.

"""
AUTHENTICATION AND OTHER AUTHORIZATION OPTIONS 
"""


class RegistrationView(APIView):
    serializer_class = RegisterSerializer

    @extend_schema(
        summary="Register user account",
        description=(
                "This endpoint allows a user to register a user account. "
                "Make sure you send 'is_agent' as `true` in your request when you want to create an agent profile. "
                "If `is_agent` is set to `true`, an agent profile is automatically created. "
                "Otherwise, a normal user profile is created.\n\n"
                "**Note:** If the user already has an existing profile, an error message indicating the kind of profile is already in use will be displayed."
                "**Note: If the user wants to create another kind of account, send the same details including the same entered password details**"
        ),
        tags=['Registration'],
        responses={
            status.HTTP_409_CONFLICT: OpenApiResponse(
                description="You already have an existing account",
            ),
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Registered successfully",
            )
        }
    )
    @transaction.atomic()
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        is_agent = request.data.get('is_agent', False)
        validated_data = serializer.validated_data
        validated_data['is_active'] = True
        email = validated_data['email']

        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # User doesn't exist, so create the requested profile
            user = User.objects.create_user(**validated_data)
            profile_model = AgentProfile if is_agent else Profile
            profile_model.objects.create(user=user)
            profile_type = "Agent" if is_agent else "Normal"
            return CustomResponse.success(message=f"{profile_type} profile registered successfully",
                                          status_code=status.HTTP_201_CREATED)

        # User exists, so check if the requested profile type already exists for the user
        profile_model = AgentProfile if is_agent else Profile
        profile_type = "Agent" if is_agent else "Normal"
        try:
            profile_model.objects.select_related('user').get(user=user)
        except profile_model.DoesNotExist:
            profile_model.objects.create(user=user)
            return CustomResponse.success(message=f"{profile_type} profile registered successfully",
                                          status_code=status.HTTP_201_CREATED)

        raise RequestError(err_code=ErrorCode.ALREADY_EXISTS, err_msg=f"{profile_type} profile already exists",
                           status_code=status.HTTP_409_CONFLICT)


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

        send_otp_email(user, email, template="email_verification.html")
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
            send_otp_email(self.request.user, email, template="email_change.html")
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
        user.email_changed = True
        user.save()
        user.otp_secret.delete()

        return CustomResponse.success(message="Email changed successfully.")


class UserLoginView(TokenObtainPairView):
    serializer_class = JWTSerializer
    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        summary="Login",
        description="""
        This endpoint authenticates a registered and verified user and provides the necessary authentication tokens.
        Make sure you don't send "is_agent" to this endpoint.
        """,
        request=LoginSerializer,
        tags=['Profile Authentication'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Logged in successfully",
                response=ProfileSerializer,
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

        user.is_agent = False
        tokens_response = JWTSerializer.get_token(user)
        tokens = {"refresh": str(tokens_response), "access": str(tokens_response.access_token)}

        if not Profile.objects.select_related('user').filter(user=user).exists():
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="You don't have a normal profile",
                               status_code=status.HTTP_404_NOT_FOUND)

        profile_serializer = ProfileSerializer(user.user_profile, context={"request": request})
        response_data = {"tokens": tokens, "profile_data": profile_serializer.data}
        return CustomResponse.success(message="Normal profile logged in successfully", data=response_data)


class AgentLoginView(TokenObtainPairView):
    serializer_class = AgentProfileSerializer
    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        summary="Login",
        description="""
        This endpoint authenticates a registered and verified user and provides the necessary authentication tokens.
        "is_agent" is True by default and it's been sent to the endpoint
        """,
        request=LoginSerializer,
        tags=['Agent Authentication'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Logged in successfully",
                response=ProfileSerializer,
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

        user.is_agent = True
        tokens_response = JWTSerializer.get_token(user)
        tokens = {"refresh": str(tokens_response), "access": str(tokens_response.access_token)}

        if not AgentProfile.objects.select_related('user').filter(user=user).exists():
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="You don't have an agent profile",
                               status_code=status.HTTP_404_NOT_FOUND)

        profile_serializer = self.serializer_class(user.agent_profile, context={"request": request})
        response_data = {"tokens": tokens, "profile_data": profile_serializer.data}
        return CustomResponse.success(message="Agent profile logged in successfully", data=response_data)


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

        send_otp_email(user, email, "forgot_password.html")
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
NORMAL PROFILE
"""


class RetrieveUpdateDeleteProfileView(APIView):
    permission_classes = (IsAuthenticatedUser,)
    serializer_class = ProfileSerializer

    @extend_schema(
        summary="Retrieve user profile",
        description=
        """
        This endpoint allows a user to retrieve his/her normal profile.
        """,
        tags=['Normal Profile'],
        responses={
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Provide a profile id"
            ),
            status.HTTP_200_OK: OpenApiResponse(
                description="Fetched successfully"
            )
        }
    )
    def get(self, request):
        user = self.request.user
        try:
            user_profile = Profile.objects.select_related('user').get(user=user)
        except Profile.DoesNotExist:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No profile found for this user",
                               status_code=status.HTTP_404_NOT_FOUND)
        serialized_data = ProfileSerializer(user_profile, context={"request": request}).data
        return CustomResponse.success(message="Retrieved profile successfully", data=serialized_data)

    @extend_schema(
        summary="Update user profile",
        description=
        """
        This endpoint allows a user to update his/her user profile.
        """,
        tags=['Normal Profile'],
        responses={
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Provide a profile id"
            ),
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                description="Updated successfully"
            )
        }
    )
    @transaction.atomic()
    def patch(self, request):
        user = self.request.user
        user_profile = Profile.objects.select_related('user').get(user=user)
        update_profile = self.serializer_class(user_profile, data=self.request.data, partial=True,
                                               context={"request": request})

        update_profile.is_valid(raise_exception=True)
        updated = self.serializer_class(update_profile.save()).data
        return CustomResponse.success(message="Updated profile successfully", data=updated,
                                      status_code=status.HTTP_202_ACCEPTED)

    @extend_schema(
        summary="Delete user profile",
        description=
        """
        This endpoint allows a user to delete his/her user profile.
        """,
        tags=['Normal Profile'],
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
        Profile.objects.select_related('user').get(user=user).delete()
        return CustomResponse.success(message="Deleted successfully")


"""
AGENT PROFILE
"""


class RetrieveUpdateDeleteAgentProfileView(APIView):
    permission_classes = (IsAuthenticatedAgent,)
    serializer_class = AgentProfileSerializer

    @extend_schema(
        summary="Retrieve agent profile",
        description=
        """
        This endpoint allows a user to retrieve his/her agent profile.
        """,
        tags=['Agent Profile'],
        responses={
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Provide a profile id"
            ),
            status.HTTP_200_OK: OpenApiResponse(
                description="Fetched successfully"
            )
        }
    )
    def get(self, request):
        user = self.request.user
        try:
            agent_profile = AgentProfile.objects.select_related('user').get(user=user)
        except AgentProfile.DoesNotExist:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No profile found for this user",
                               status_code=status.HTTP_404_NOT_FOUND)

        serialized_data = self.serializer_class(agent_profile, context={"request": request}).data
        return CustomResponse.success(message="Retrieved profile successfully", data=serialized_data)

    @extend_schema(
        summary="Update agent profile",
        description=
        """
        This endpoint allows a user to update his/her agent profile.
        """,
        tags=['Agent Profile'],
        responses={
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Provide a profile id"
            ),
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                description="Updated successfully"
            )
        }
    )
    @transaction.atomic()
    def patch(self, request):
        user = self.request.user
        agent_profile = AgentProfile.objects.select_related('user').get(user=user)
        update_profile = self.serializer_class(agent_profile, data=self.request.data, partial=True,
                                               context={"request": request})

        update_profile.is_valid(raise_exception=True)
        updated = self.serializer_class(update_profile.save()).data
        return CustomResponse.success(message="Updated profile successfully", data=updated,
                                      status_code=status.HTTP_202_ACCEPTED)

    @extend_schema(
        summary="Delete agent profile",
        description=
        """
        This endpoint allows a user to delete his/her agent profile.
        """,
        tags=['Agent Profile'],
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
        AgentProfile.objects.select_related('user').get(user=user).delete()
        return CustomResponse.success(message="Deleted successfully")
