from datetime import timedelta

import pyotp
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.utils import timezone
from faker import Faker
from rest_framework.test import APIClient, APITestCase

from apps.core.models import OTPSecret


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

    def _employee_registration_success(self):
        # Test successful registration
        response = self.client.post(reverse_lazy('employee-registration'), data=self.user_data)
        self.assertEqual(response.status_code, 201)
        employee = self.user.objects.get()
        return employee

    def _email_verification_success(self):
        # Using employee for the verification process since its similar to the company
        employee = self._employee_registration_success()

        # Test successful email verification
        otp_secret = OTPSecret.objects.get(user=employee)

        # Generate the OTP using the secret
        totp = pyotp.TOTP(otp_secret.secret, interval=600)
        otp = totp.now()

        user_data = {'email': employee.email, 'otp': otp}

        response = self.client.post(reverse_lazy('verify-email'), data=user_data)
        assert response.status_code == 200
        assert 'Email verification successful' in response.data.get('message')
        return employee, otp_secret

    def _login_success(self):
        # Test with registered employee profile
        employee, _ = self._email_verification_success()

        user_data = {"email": employee.email, "password": 'test_password'}

        response = self.client.post(reverse_lazy('login'), data=user_data)
        assert response.status_code == 200
        assert 'Logged in successfully' in response.data.get('message')
        assert 'tokens' in response.data.get('data')
        assert 'profile_data' in response.data.get('data')
        tokens = response.data.get('data').get('tokens')
        profile_data = response.data.get('data').get('profile_data')
        return tokens, profile_data

    def _authenticate_with_tokens(self):
        tokens, _ = self._login_success()
        self.client.force_authenticate(user=self.user.objects.get(), token=tokens.get('access'))

    def _company_registration_success(self):
        # Test successful registration
        response = self.client.post(reverse_lazy('company-registration'), data=self.user_data)
        assert response.status_code == 201
        company = self.user.objects.get()
        return company

    def test_employee_registration_conflict(self):
        already_registered_user = self._employee_registration_success()

        data = {"email": already_registered_user.email, "password": already_registered_user.password}

        # Test registration with existing user
        response = self.client.post(reverse_lazy('employee-registration'), data=data)
        assert response.status_code == 409

    def test_company_registration_conflict(self):
        already_registered_user = self._company_registration_success()

        data = {"email": already_registered_user.email, "password": already_registered_user.password}

        response = self.client.post(reverse_lazy('company-registration'), data=data)
        assert response.status_code == 409

    def test_already_verified_user(self):
        # Test email verification for an already verified user
        employee, otp_secret = self._email_verification_success()

        # Generate the OTP using the secret
        totp = pyotp.TOTP(otp_secret.secret, interval=600)
        otp = totp.now()
        user_data = {'email': employee.email, 'otp': otp}

        response = self.client.post(reverse_lazy('verify-email'), data=user_data)
        assert response.status_code == 200
        assert 'Email verified already' in response.data.get('message')

    def test_expired_otp(self):
        # Test email verification for an already verified user
        employee, otp_secret = self._email_verification_success()

        # Create a new otp secret since after each use of a otp the secret is always deleted
        otp_secret = OTPSecret.objects.create(user=employee, secret=pyotp.random_base32(),
                                              created=timezone.now() - timedelta(minutes=20))

        # Generate the OTP using the secret
        totp = pyotp.TOTP(otp_secret.secret, interval=600)
        otp = totp.now()
        user_data = {'email': 'test@example.com', 'otp': otp}

        response = self.client.post(reverse_lazy('verify-email'), data=user_data)
        if timezone.now() > otp_secret.created + timedelta(minutes=20):
            assert response.status_code == 400
            assert 'OTP has expired' in response.data.get('message')

    def test_non_existent_user(self):
        # Test email verification for a non-existent user
        user_data = {'email': 'nonexistent@example.com', 'otp': '123456'}

        response = self.client.post(reverse_lazy('verify-email'), data=user_data)
        assert response.status_code == 404
        assert 'User with this email not found' in response.data.get('message')

    def test_resend_verification_code_success(self):
        employee = self._employee_registration_success()
        user_data = {'email': employee.email}

        response = self.client.post(reverse_lazy('resend-email-verification-code'), data=user_data)
        assert response.status_code == 200
        assert 'Verification code sent successfully' in response.data.get('message')

    def test_resend_verification_code_already_verified_user(self):
        # Test resend of verification code for an already verified user
        employee, _ = self._email_verification_success()
        user_data = {'email': employee.email}

        response = self.client.post(reverse_lazy('resend-email-verification-code'), data=user_data)
        assert response.status_code == 200
        assert 'Email already verified' in response.data.get('message')

    def test_resend_verification_code_non_existent_user(self):
        # Test resend of verification code for a non-existent user
        user_data = {'email': 'nonexistent@example.com'}

        response = self.client.post(reverse_lazy('resend-email-verification-code'), data=user_data)
        assert response.status_code == 404
        assert 'User with this email not found' in response.data.get('message')

    def test_login_unverified_email(self):
        # Test login with unverified email
        employee = self._employee_registration_success()

        user_data = {"email": employee.email, "password": 'test_password'}

        response = self.client.post(reverse_lazy('login'), data=user_data)
        assert response.status_code == 400
        assert 'Verify your email first' in response.data.get('message')

    def test_login_invalid_credentials(self):
        # Test login with invalid credentials
        employee, _ = self._email_verification_success()
        user_data = {"email": employee.email, "password": 'wrong_password'}

        response = self.client.post(reverse_lazy('login'), data=user_data)
        assert response.status_code == 401
        assert 'Invalid credentials' in response.data.get('message')

    def test_change_email_success(self):
        self._authenticate_with_tokens()
        user = self.user.objects.get()

        otp_secret = OTPSecret.objects.create(user=user, secret=pyotp.random_base32())
        totp = pyotp.TOTP(otp_secret.secret, interval=600)
        otp = totp.now()

        user_data = {'email': 'new@example.com', 'otp': otp}

        response = self.client.post(reverse_lazy('change-email'), data=user_data)
        assert response.status_code == 200
        assert 'Email changed successfully' in response.data.get('message')

    def test_change_email_old_email(self):
        self._authenticate_with_tokens()
        user = self.user.objects.get()

        # Test change of email with the same email as the current one
        otp_secret = OTPSecret.objects.create(user=user, secret=pyotp.random_base32())
        totp = pyotp.TOTP(otp_secret.secret, interval=600)
        otp = totp.now()

        user_data = {'email': 'test@example.com', 'otp': otp}

        response = self.client.post(reverse_lazy('change-email'), data=user_data)
        assert response.status_code == 403
        assert 'You can\'t use your previous email' in response.data.get('message')

    def test_change_email_no_otp_found(self):
        self._authenticate_with_tokens()
        user = self.user.objects.get()

        if not OTPSecret.objects.filter(user=user).exists():
            user_data = {'email': 'new@example.com', 'otp': '123456'}

            response = self.client.post(reverse_lazy('change-email'), data=user_data)
            assert response.status_code == 404
            assert 'No OTP found for this account' in response.data.get('message')

    def test_change_email_expired_otp(self):
        self._authenticate_with_tokens()
        user = self.user.objects.get()

        # Test change of email with the same email as the current one
        otp_secret = OTPSecret.objects.create(user=user, secret=pyotp.random_base32())
        otp_secret.created -= timedelta(minutes=20)
        otp_secret.save()

        totp = pyotp.TOTP(otp_secret.secret, interval=600)
        otp = totp.now()
        user_data = {'email': 'new@example.com', 'otp': otp}

        response = self.client.post(reverse_lazy('change-email'), data=user_data)
        assert response.status_code == 400
        assert 'OTP has expired' in response.data.get('message')

    def test_change_email_incorrect_otp(self):
        self._authenticate_with_tokens()
        user = self.user.objects.get()

        otp_secret = OTPSecret.objects.create(user=user, secret=pyotp.random_base32())
        totp = pyotp.TOTP(otp_secret.secret, interval=600)

        user_data = {'email': 'new@example.com', 'otp': '12345'}

        response = self.client.post(reverse_lazy('change-email'), data=user_data)
        assert response.status_code == 400
        assert 'Invalid OTP' in response.data.get('message')
