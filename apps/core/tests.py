from datetime import timedelta

import pyotp
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import check_password
from django.urls import reverse_lazy
from django.utils import timezone
from faker import Faker
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from apps.core.models import EmployeeProfile, CompanyProfile, OTPSecret


class TestCoreEndpoints(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.fake = Faker()
        cls.user = get_user_model()

    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'email': 'test@example.com',
            'password': 'test_password',
        }

    def test_employee_registration_success(self):
        # Test successful registration
        response = self.client.post(reverse_lazy('employee-registration'), data=self.user_data)
        assert response.status_code == 201

    def test_employee_registration_conflict(self):
        # Test registration with existing user
        existing_user = self.user.objects.create_user(email='existing@example.com', password='existing_password')
        EmployeeProfile.objects.create(user=existing_user)

        data = {
            'email': 'existing@example.com',
            'password': 'new_password',
        }

        response = self.client.post(reverse_lazy('employee-registration'), data=data)
        assert response.status_code == 409

    def test_company_registration_success(self):
        # Test successful registration
        response = self.client.post(reverse_lazy('company-registration'), data=self.user_data)
        assert response.status_code == 201

    def test_company_registration_conflict(self):
        # Test registration with existing user
        existing_user = self.user.objects.create_user(email='existing@example.com', password='existing_password')
        CompanyProfile.objects.create(user=existing_user)

        data = {
            'email': 'existing@example.com',
            'password': 'new_password',
        }

        response = self.client.post(reverse_lazy('company-registration'), data=data)
        assert response.status_code == 409

    def test_email_verification_success(self):
        # Test successful email verification
        user = self.user.objects.create(email='test@example.com', email_verified=False)
        otp_secret = OTPSecret.objects.create(user=user, secret=pyotp.random_base32())

        # Generate the OTP using the secret
        totp = pyotp.TOTP(otp_secret.secret, interval=600)
        otp = totp.now()
        user_data = {'email': 'test@example.com', 'otp': otp}

        response = self.client.post(reverse_lazy('verify-email'), data=user_data)
        assert response.status_code == 200
        assert 'Email verification successful' in response.data.get('message')

    def test_already_verified_user(self):
        # Test email verification for an already verified user
        user = self.user.objects.create(email='test@example.com', email_verified=True)
        otp_secret = OTPSecret.objects.create(user=user, secret=pyotp.random_base32())

        # Generate the OTP using the secret
        totp = pyotp.TOTP(otp_secret.secret, interval=600)
        otp = totp.now()
        user_data = {'email': 'test@example.com', 'otp': otp}

        response = self.client.post(reverse_lazy('verify-email'), data=user_data)
        assert response.status_code == 200
        assert 'Email verified already' in response.data.get('message')

    def test_invalid_otp(self):
        # Test email verification with invalid OTP
        user = self.user.objects.create(email='test@example.com', email_verified=False)
        otp_secret = OTPSecret.objects.create(user=user, secret=pyotp.random_base32())

        # Generate the OTP using the secret
        totp = pyotp.TOTP(otp_secret.secret, interval=600)
        otp = totp.now()
        user_data = {'email': 'test@example.com', 'otp': '22222'}

        response = self.client.post(reverse_lazy('verify-email'), data=user_data)
        assert response.status_code == 400
        assert 'Invalid OTP' in response.data.get('message')

    def test_expired_otp(self):
        # Test email verification with expired OTP
        user = self.user.objects.create(email='test@example.com', email_verified=False)
        otp_secret = OTPSecret.objects.create(user=user, secret=pyotp.random_base32(),
                                              created=timezone.now() - timedelta(minutes=20))

        # Generate the OTP using the secret
        totp = pyotp.TOTP(otp_secret.secret, interval=600)
        otp = totp.now()
        user_data = {'email': 'test@example.com', 'otp': otp}

        response = self.client.post(reverse_lazy('verify-email'), data=user_data)
        if timezone.now() > otp_secret.created + timedelta(minutes=10):
            assert response.status_code == 400
            assert 'OTP has expired' in response.data.get('message')

    def test_non_existent_user(self):
        # Test email verification for a non-existent user
        user_data = {'email': 'nonexistent@example.com', 'otp': '123456'}

        response = self.client.post(reverse_lazy('verify-email'), data=user_data)
        assert response.status_code == 404
        assert 'User with this email not found' in response.data.get('message')

    def test_no_otp_secret_and_otp_found(self):
        # Test email verification when no OTP secret is found for the account
        user = self.user.objects.create(email='test@example.com', email_verified=False)
        user_data = {'email': 'test@example.com', 'otp': '123456'}

        response = self.client.post(reverse_lazy('verify-email'), data=user_data)
        assert response.status_code == 404
        assert 'No OTP secret found for this account' in response.data.get('message')

    def test_resend_verification_code_success(self):
        # Test successful resend of verification code
        user = self.user.objects.create(email='test@example.com', email_verified=False)
        user_data = {'email': 'test@example.com'}

        response = self.client.post(reverse_lazy('resend-email-verification-code'), data=user_data)
        assert response.status_code == 200
        assert 'Verification code sent successfully' in response.data.get('message')

    def test_resend_verification_code_already_verified_user(self):
        # Test resend of verification code for an already verified user
        user = self.user.objects.create(email='test@example.com', email_verified=True)
        user_data = {'email': 'test@example.com'}

        response = self.client.post(reverse_lazy('resend-email-verification-code'), data=user_data)
        assert response.status_code == 200
        assert 'Email already verified' in response.data.get('message')

    def test_resend_verification_code_non_existent_user(self):
        # Test resend of verification code for a non-existent user
        user_data = {'email': 'nonexistent@example.com'}

        response = self.client.post(reverse_lazy('resend-email-verification-code'), data=user_data)
        assert response.status_code == 404
        assert 'User with this email not found' in response.data.get('message')

    def create_user_and_employee_profile(self, email, password, email_verified=True):
        # since company and employee has the same pattern of creation, i'm going with employee for the test cases
        user = self.user.objects.create_user(email=email, password=password, email_verified=email_verified)
        profile = EmployeeProfile.objects.create(user=user)
        return user, profile

    def test_login_success(self):
        # Test successful login
        user, _ = self.create_user_and_employee_profile('test@example.com', 'test_password', email_verified=True)
        user_data = {'email': user.email, 'password': 'test_password'}

        authenticated_user = authenticate(request=self.client, **user_data)
        print(authenticated_user)
        assert authenticated_user is not None, "Invalid credentials"

        response = self.client.post(reverse_lazy('login'), data=user_data)
        assert response.status_code == 200
        assert 'Logged in successfully' in response.data.get('message')
        assert 'tokens' in response.data.get('data')
        assert 'profile_data' in response.data.get('data')
        token = Token.objects.create(user=user)
        self.client.force_authenticate(user=user, token=token.key)

    def test_login_unverified_email(self):
        # Test login with unverified email
        user, _ = self.create_user_and_profiles('test@example.com', 'test_password', email_verified=False)
        user_data = {'email': 'test@example.com', 'password': 'test_password'}

        response = self.client.post(reverse_lazy('login'), data=user_data)
        assert response.status_code == 400
        assert 'Verify your email first' in response.data.get('message')

    def test_login_invalid_credentials(self):
        # Test login with invalid credentials
        self.user.objects.create_user(email='test@example.com', password='test_password', email_verified=True)
        user_data = {'email': 'test@example.com', 'password': 'wrong_password'}

        response = self.client.post(reverse_lazy('login'), data=user_data)
        assert response.status_code == 401
        assert 'Invalid credentials' in response.data.get('message')

    def test_change_email_success(self):
        # Test successful change of email
        user = self.user.objects.create(email='test@example.com', email_verified=True)
        otp_secret = OTPSecret.objects.create(user=user, secret=pyotp.random_base32(),
                                              created=timezone.now() - timedelta(minutes=20))

        # Generate the OTP using the secret
        totp = pyotp.TOTP(otp_secret.secret, interval=600)
        otp = totp.now()
        user_data = {'email': 'new@example.com', 'code': otp}

        response = self.client.post(reverse_lazy('change-email'), data=user_data)
        print(response)
        assert response.status_code == 200
        assert 'Email changed successfully' in response.data.get('message')

    def test_change_email_old_email(self):
        # Test change of email with the same email as the current one
        user = self.user.objects.create(email='test@example.com', email_verified=True)
        otp_secret = OTPSecret.objects.create(user=user, secret=pyotp.random_base32())
        user_data = {'email': 'test@example.com', 'code': '121212'}

        response = self.client.post(reverse_lazy('change-email'), data=user_data)
        assert response.status_code == 403
        assert 'You can\'t use your previous email' in response.data.get('message')

    def test_change_email_no_otp_found(self):
        # Test change of email without OTP found
        user = self.user.objects.create(email='test@example.com', email_verified=True)
        user_data = {'email': 'new@example.com', 'code': '121212'}

        response = self.client.post(reverse_lazy('change-email'), data=user_data)
        assert response.status_code == 404
        assert 'No OTP found for this account' in response.data.get('message')

    def test_change_email_expired_otp(self):
        # Test change of email with an expired OTP
        user = self.user.objects.create(email='test@example.com', email_verified=True)
        otp_secret = OTPSecret.objects.create(user=user, secret=pyotp.random_base32())
        otp_secret.created = otp_secret.created - timedelta(minutes=11)  # Simulate an expired OTP
        otp_secret.save()

        user_data = {'email': 'new@example.com', 'code': 'test_code'}

        response = self.client.post(reverse_lazy('change-email'), data=user_data)
        assert response.status_code == 400
        assert 'OTP has expired' in response.data.get('message')

    def test_change_email_incorrect_otp(self):
        # Test change of email with an incorrect OTP
        user = self.user.objects.create(email='test@example.com', email_verified=True)
        otp_secret = OTPSecret.objects.create(user=user, secret=pyotp.random_base32())

        user_data = {'email': 'new@example.com', 'code': 'incorrect_code'}

        response = self.client.post(reverse_lazy('change-email'), data=user_data)
        assert response.status_code == 400
        assert 'Invalid OTP' in response.data.get('message')
