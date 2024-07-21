import pyotp
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer, TokenObtainPairSerializer, \
    TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenBlacklistView, TokenRefreshView

from apps.common.permissions import IsAuthenticatedEmployee, IsAuthenticatedCompany
from apps.common.responses import CustomResponse
from apps.core.docs.docs import *
from apps.core.emails import send_otp_email
from apps.core.selectors import *
from apps.core.serializers import *
from apps.notification.choices import NOTIFICATION_PROFILE_UPDATED
from apps.notification.models import Notification
from utilities.encryption import decrypt_token_to_profile, encrypt_profile_to_token

User = get_user_model()

# Create your views here.


"""
REGISTRATION
"""


class EmployeeRegistrationView(APIView):
    serializer_class = RegisterSerializer

    @employee_registration_docs()
    @transaction.atomic
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        email = data.get('email')

        employee_instance, user = create_employee_profile(email=email, data=data)

        # Generate one time otp secret
        otp_secret = pyotp.random_base32()

        data = {
            "secret": otp_secret,
            "user_data": EmployeeProfileSerializer(employee_instance).data
        }

        send_otp_email(otp_secret=otp_secret, recipient=user, template='email_verification.html')
        return CustomResponse.success(message="Registration successful, check your email for verification.",
                                      status_code=status.HTTP_201_CREATED, data=data)


class CompanyRegistrationView(APIView):
    serializer_class = RegisterSerializer

    @company_registration_docs()
    @transaction.atomic
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        email = data.get('email')

        company_instance, user = create_company_profile(email=email, data=data)

        # Generate one time otp secret
        otp_secret = pyotp.random_base32()

        data = {
            "secret": otp_secret,
            "user_data": CompanyProfileSerializer(company_instance).data
        }

        send_otp_email(otp_secret=otp_secret, recipient=user, template='email_verification.html')
        return CustomResponse.success(message="Registration successful, check your email for verification.",
                                      status_code=status.HTTP_201_CREATED, data=data)


"""
AUTHENTICATION AND VERIFICATION OPTIONS 
"""


class VerifyEmailView(APIView):
    serializer_class = VerifyEmailSerializer

    @verify_email_docs()
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        otp_secret = kwargs.get('otp_secret')

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')
        code = request.data.get('otp')

        user = get_existing_user(email=email)

        if user.email_verified:
            raise RequestError(err_code=ErrorCode.VERIFIED_USER, err_msg="Email verified already",
                               status_code=status.HTTP_200_OK)

        otp_verification(otp_secret=otp_secret, code=code)

        # OTP verification successful
        user.email_verified = True
        user.save()

        return CustomResponse.success(message="Email verification successful.")


class ResendEmailVerificationCodeView(APIView):
    serializer_class = ResendEmailVerificationCodeSerializer

    @resend_email_verification_code_docs()
    @transaction.atomic
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        user = get_existing_user(email=email)

        if user.email_verified:
            raise RequestError(err_code=ErrorCode.VERIFIED_USER, err_msg="Email already verified",
                               status_code=status.HTTP_200_OK)

        # Generate OTP secret for the user
        otp_secret = pyotp.random_base32()

        send_otp_email(otp_secret=otp_secret, recipient=user, template="email_verification.html")

        data = {'otp_secret': otp_secret}
        return CustomResponse.success("Verification code sent successfully. Please check your mail", data=data)


class SendNewEmailVerificationCodeView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SendNewEmailVerificationCodeSerializer

    @send_new_email_verification_code_docs()
    @transaction.atomic
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        check_existing_user(email=email)

        otp_secret = pyotp.random_base32()

        # send email if the email is new
        send_otp_email(otp_secret=otp_secret, recipient=email, template="email_change.html")

        data = {'otp_secret': otp_secret}
        return CustomResponse.success("Verification code sent successfully. Please check your mail", data=data)


class ChangeEmailView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangeEmailSerializer

    @change_email_docs()
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        otp_secret = kwargs.get('otp_secret')

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_email = serializer.validated_data.get('email')
        code = request.data.get('otp')
        user = request.user

        otp_verification(otp_secret=otp_secret, code=code)

        if user.email == new_email:
            raise RequestError(err_code=ErrorCode.OLD_EMAIL, err_msg="You can't use your previous email",
                               status_code=status.HTTP_403_FORBIDDEN)

        user.email = new_email
        user.save()

        return CustomResponse.success(message="Email changed successfully.")


class LoginView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

    @login_docs()
    @transaction.atomic
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        # authenticating user
        user = authenticate(request, email=email, password=password)

        if not user:
            raise RequestError(err_code=ErrorCode.INVALID_CREDENTIALS, err_msg="Invalid credentials",
                               status_code=status.HTTP_401_UNAUTHORIZED)

        if not user.email_verified:
            raise RequestError(err_code=ErrorCode.UNVERIFIED_USER, err_msg="Verify your email first",
                               status_code=status.HTTP_400_BAD_REQUEST)

        # Checking the type of profile it is (employee or company) and adding the data to the response
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

    @logout_docs()
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

    @refresh_docs()
    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
        except TokenError:
            raise RequestError(err_code=ErrorCode.INVALID_ENTRY, err_msg="Error refreshing token",
                               status_code=status.HTTP_400_BAD_REQUEST)

        access_token = serializer.validated_data['access']
        return CustomResponse.success(message="Refreshed successfully", data=access_token)


class RequestForgotPasswordCodeView(APIView):
    serializer_class = RequestNewPasswordCodeSerializer

    @request_forgot_password_code_docs()
    @transaction.atomic
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        user = get_existing_user(email=email)

        # Generate OTP secret for the user
        otp_secret = pyotp.random_base32()

        send_otp_email(otp_secret=otp_secret, recipient=user, template="forgot_password.html")

        data = {
            "otp_secret": otp_secret
        }
        return CustomResponse.success(message="Password code sent successfully", data=data)


class VerifyForgotPasswordCodeView(APIView):
    serializer_class = VerifyEmailSerializer

    @verify_forgot_password_code_docs()
    def post(self, request, *args, **kwargs):
        otp_secret = kwargs.get('otp_secret')

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get("email")
        code = request.data.get("otp")

        user = get_existing_user(email=email)

        otp_verification(otp_secret=otp_secret, code=code)

        token = encrypt_profile_to_token(user)  # Encrypt the user profile to a token.
        return CustomResponse.success(message="Otp verified successfully", data=token)


class ChangeForgottenPasswordView(APIView):
    serializer_class = ChangePasswordSerializer

    @change_forgotten_password_docs()
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        token = kwargs.get('token')

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

    @change_password_docs()
    @transaction.atomic
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

    @retrieve_employee_profile_docs()
    def get(self, request):
        user = request.user

        cache_key = f"employee_profile_{user.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return CustomResponse.success(message="Retrieved profile successfully", data=cached_data)

        profile_instance = get_employee_profile(user=user)

        serialized_data = self.serializer_class(profile_instance, context={"request": request}).data

        # Set cache data
        cache.set(cache_key, serialized_data, timeout=60 * 60 * 24)
        return CustomResponse.success(message="Retrieved profile successfully", data=serialized_data)

    @update_employee_profile_docs()
    @transaction.atomic
    def patch(self, request):
        user = request.user

        profile_instance = get_employee_profile(user=user)

        update_profile = self.serializer_class(profile_instance, data=request.data, partial=True)
        update_profile.is_valid(raise_exception=True)
        updated = self.serializer_class(update_profile.save()).data

        Notification.objects.create(user=user, notification_type=NOTIFICATION_PROFILE_UPDATED,
                                    message="Profile updated successfully")

        return CustomResponse.success(message="Updated profile successfully", data=updated,
                                      status_code=status.HTTP_202_ACCEPTED)

    @delete_employee_profile_docs()
    def delete(self, request):
        user = request.user
        user.delete()
        return CustomResponse.success(message="Account deleted successfully", status_code=status.HTTP_204_NO_CONTENT)


"""
COMPANY PROFILE
"""


class RetrieveUpdateDeleteCompanyProfileView(APIView):
    permission_classes = (IsAuthenticatedCompany,)
    serializer_class = CompanyProfileSerializer

    @retrieve_company_profile_docs()
    def get(self, request):
        user = request.user

        cache_key = f"company_profile_{user.id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return CustomResponse.success(message="Retrieved profile successfully", data=cached_data)

        profile_instance = get_company_profile(user=user)

        serialized_data = self.serializer_class(profile_instance, context={"request": request}).data

        # Set cache data
        cache.set(cache_key, serialized_data, timeout=60 * 60 * 24)
        return CustomResponse.success(message="Retrieved profile successfully", data=serialized_data)

    @update_company_profile_docs()
    @transaction.atomic
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

    @delete_company_profile_docs()
    def delete(self, request):
        user = request.user
        user.delete()
        return CustomResponse.success(message="Account deleted successfully", status_code=status.HTTP_204_NO_CONTENT)
