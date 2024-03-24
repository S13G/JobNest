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
        self.tokens = ''
        self.encrypted_password_token = ''

        # Store URLs in variables
        self.employee_registration_url = reverse_lazy('employee-registration')
        self.company_registration_url = reverse_lazy('company-registration')
        self.verify_email_url = reverse_lazy('verify-email')
        self.login_url = reverse_lazy('login')
        self.logout_url = reverse_lazy('logout')
        self.change_email_url = reverse_lazy('change-email')
        self.request_forgotten_password_code_url = reverse_lazy('request-forgotten-password-code')
        self.change_forgotten_password_url = reverse_lazy('change-forgotten-password')
        self.verify_forgot_password_code_url = reverse_lazy('verify-forgotten-password-code')
        self.change_password_url = reverse_lazy('change-password')
        self.resend_email_verification_code_url = reverse_lazy('resend-email-verification-code')
        self.send_new_email_verification_code_url = reverse_lazy('send-new-email-verification-code')
        self.refresh_token_url = reverse_lazy('refresh-token')
        self.employee_profile_methods_url = reverse_lazy('get-update-delete-employee-profile')
        self.company_profile_methods_url = reverse_lazy('get-update-delete-company-profile')

    def _employee_registration_success(self):
        # Test successful registration
        response = self.client.post(self.employee_registration_url, data=self.user_data)
        self.assertEqual(response.status_code, 201)
        employee = self.user.objects.get()
        return employee

    def _company_registration_success(self):
        # Test successful registration
        response = self.client.post(self.company_registration_url, data=self.user_data)
        self.assertEqual(response.status_code, 201)
        company = self.user.objects.get()
        return company

    def _email_verification_success(self):
        # Using employee for the verification process since it's similar to the company
        employee = self._employee_registration_success()

        # Test successful email verification
        otp_secret = OTPSecret.objects.get(user=employee)

        # Generate the OTP using the secret
        totp = pyotp.TOTP(otp_secret.secret, interval=600)
        otp = totp.now()

        user_data = {'email': employee.email, 'otp': otp}

        response = self.client.post(self.verify_email_url, data=user_data)
        assert response.status_code == 200
        assert 'Email verification successful' in response.data.get('message')
        return employee, otp_secret

    def _company_email_verification_success(self):
        # Using company for the verification process
        company = self._company_registration_success()

        # Test successful email verification
        otp_secret = OTPSecret.objects.get(user=company)

        # Generate the OTP using the secret
        totp = pyotp.TOTP(otp_secret.secret, interval=600)
        otp = totp.now()

        user_data = {'email': company.email, 'otp': otp}

        response = self.client.post(self.verify_email_url, data=user_data)
        assert response.status_code == 200
        assert 'Email verification successful' in response.data.get('message')
        return company, otp_secret

    def _login_success(self):
        # Test with registered employee profile
        employee, _ = self._email_verification_success()

        user_data = {"email": employee.email, "password": 'test_password'}

        response = self.client.post(self.login_url, data=user_data)
        assert response.status_code == 200
        assert 'Logged in successfully' in response.data.get('message')
        assert 'tokens' in response.data.get('data')
        assert 'profile_data' in response.data.get('data')
        tokens = response.data.get('data').get('tokens')
        profile_data = response.data.get('data').get('profile_data')
        return tokens, profile_data

    def _company_login_success(self):
        # Test with registered company profile
        company, _ = self._company_email_verification_success()

        user_data = {"email": company.email, "password": 'test_password'}

        response = self.client.post(self.login_url, data=user_data)
        assert response.status_code == 200
        assert 'Logged in successfully' in response.data.get('message')
        assert 'tokens' in response.data.get('data')
        assert 'profile_data' in response.data.get('data')
        tokens = response.data.get('data').get('tokens')
        profile_data = response.data.get('data').get('profile_data')
        return tokens, profile_data

    def _authenticate_with_tokens(self):
        tokens, _ = self._login_success()
        self.tokens = tokens
        self.client.force_authenticate(user=self.user.objects.get(), token=tokens.get('access'))

    def _authenticate_with_company_tokens(self):
        tokens, _ = self._company_login_success()
        self.tokens = tokens
        self.client.force_authenticate(user=self.user.objects.get(), token=tokens.get('access'))

    # This test case will be used in another test that calls it because of the value it possesses
    def _verify_forgot_password_code(self):
        self._authenticate_with_tokens()
        user = self.user.objects.get()

        otp_secret = OTPSecret.objects.create(user=user, secret=pyotp.random_base32())
        totp = pyotp.TOTP(otp_secret.secret, interval=600)
        otp = totp.now()
        data = {"email": user.email, "otp": otp}

        response = self.client.post(self.verify_forgot_password_code_url, data=data)
        assert response.status_code == 200
        assert "Otp verified successfully" in response.data.get('message')
        self.encrypted_password_token = response.data.get('data')

        # Test with non-existent user
        data = {"email": "nonexistent@example.com", "otp": "123456"}
        response = self.client.post(self.verify_forgot_password_code_url, data=data)
        assert response.status_code == 404
        assert "User with this email not found" in response.data.get('message')

        # Test with invalid otp
        data = {"email": user.email, "otp": "123456"}
        response = self.client.post(self.verify_forgot_password_code_url, data=data)
        assert response.status_code == 400
        assert "Invalid OTP" in response.data.get('message')

        # Test with expired otp
        otp_secret.created -= timedelta(minutes=20)
        otp_secret.save()

        totp = pyotp.TOTP(otp_secret.secret, interval=600)
        otp = totp.now()

        data = {"email": user.email, "otp": otp}

        response = self.client.post(self.verify_forgot_password_code_url, data=data)
        assert response.status_code == 400
        assert "OTP has expired" in response.data.get('message')

        # Test with no otp secret
        otp_secret.delete()

        if not OTPSecret.objects.filter(user=user).exists():
            user_data = {'email': user.email, 'otp': '123456'}

            response = self.client.post(self.verify_forgot_password_code_url, data=user_data)
            assert response.status_code == 404
            assert 'No OTP found for this account' in response.data.get('message')

    def test_employee_registration_conflict(self):
        already_registered_user = self._employee_registration_success()

        data = {"email": already_registered_user.email, "password": already_registered_user.password}

        # Test registration with existing user
        response = self.client.post(self.employee_registration_url, data=data)
        assert response.status_code == 409

    def test_company_registration_conflict(self):
        already_registered_user = self._company_registration_success()

        data = {"email": already_registered_user.email, "password": already_registered_user.password}

        response = self.client.post(self.company_registration_url, data=data)
        assert response.status_code == 409

    def test_already_verified_user(self):
        # Test email verification for an already verified user
        employee, otp_secret = self._email_verification_success()

        # Generate the OTP using the secret
        totp = pyotp.TOTP(otp_secret.secret, interval=600)
        otp = totp.now()
        user_data = {'email': employee.email, 'otp': otp}

        response = self.client.post(self.verify_email_url, data=user_data)
        assert response.status_code == 200
        assert 'Email verified already' in response.data.get('message')

    def test_expired_otp(self):
        # Test email verification for an already verified user
        employee, otp_secret = self._email_verification_success()

        # Create a new otp secret since after each use of otp the secret is always deleted
        otp_secret = OTPSecret.objects.create(user=employee, secret=pyotp.random_base32(),
                                              created=timezone.now() - timedelta(minutes=20))

        # Generate the OTP using the secret
        totp = pyotp.TOTP(otp_secret.secret, interval=600)
        otp = totp.now()
        user_data = {'email': 'test@example.com', 'otp': otp}

        response = self.client.post(self.verify_email_url, data=user_data)
        if timezone.now() > otp_secret.created + timedelta(minutes=20):
            assert response.status_code == 400
            assert 'OTP has expired' in response.data.get('message')

    def test_non_existent_user(self):
        # Test email verification for a non-existent user
        user_data = {'email': 'nonexistent@example.com', 'otp': '123456'}

        response = self.client.post(self.verify_email_url, data=user_data)
        assert response.status_code == 404
        assert 'User with this email not found' in response.data.get('message')

    def test_resend_verification_code_success(self):
        employee = self._employee_registration_success()
        user_data = {'email': employee.email}

        response = self.client.post(self.resend_email_verification_code_url, data=user_data)
        assert response.status_code == 200
        assert 'Verification code sent successfully' in response.data.get('message')

    def test_resend_verification_code_already_verified_user(self):
        # Test resend of verification code for an already verified user
        employee, _ = self._email_verification_success()
        user_data = {'email': employee.email}

        response = self.client.post(self.resend_email_verification_code_url, data=user_data)
        assert response.status_code == 200
        assert 'Email already verified' in response.data.get('message')

    def test_resend_verification_code_non_existent_user(self):
        # Test resend of verification code for a non-existent user
        user_data = {'email': 'nonexistent@example.com'}

        response = self.client.post(self.resend_email_verification_code_url, data=user_data)
        assert response.status_code == 404
        assert 'User with this email not found' in response.data.get('message')

    def test_login_unverified_email(self):
        # Test login with unverified email
        employee = self._employee_registration_success()

        user_data = {"email": employee.email, "password": 'test_password'}

        response = self.client.post(self.login_url, data=user_data)
        assert response.status_code == 400
        assert 'Verify your email first' in response.data.get('message')

    def test_login_invalid_credentials(self):
        # Test login with invalid credentials
        employee, _ = self._email_verification_success()
        user_data = {"email": employee.email, "password": 'wrong_password'}

        response = self.client.post(self.login_url, data=user_data)
        assert response.status_code == 401
        assert 'Invalid credentials' in response.data.get('message')

    def test_change_email_success(self):
        self._authenticate_with_tokens()
        user = self.user.objects.get()

        otp_secret = OTPSecret.objects.create(user=user, secret=pyotp.random_base32())
        totp = pyotp.TOTP(otp_secret.secret, interval=600)
        otp = totp.now()

        user_data = {'email': 'new@example.com', 'otp': otp}

        response = self.client.post(self.change_email_url, data=user_data)
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

        response = self.client.post(self.change_email_url, data=user_data)
        assert response.status_code == 403
        assert 'You can\'t use your previous email' in response.data.get('message')

    def test_change_email_no_otp_found(self):
        self._authenticate_with_tokens()
        user = self.user.objects.get()

        if not OTPSecret.objects.filter(user=user).exists():
            user_data = {'email': 'new@example.com', 'otp': '123456'}

            response = self.client.post(self.change_email_url, data=user_data)
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

        response = self.client.post(self.change_email_url, data=user_data)
        assert response.status_code == 400
        assert 'OTP has expired' in response.data.get('message')

    def test_change_email_incorrect_otp(self):
        self._authenticate_with_tokens()
        user = self.user.objects.get()

        OTPSecret.objects.create(user=user, secret=pyotp.random_base32())

        user_data = {'email': 'new@example.com', 'otp': '12345'}

        response = self.client.post(self.change_email_url, data=user_data)
        assert response.status_code == 400
        assert 'Invalid OTP' in response.data.get('message')

    def test_send_new_email_verification_code(self):
        self._authenticate_with_tokens()
        data = {"email": "new@example.com"}

        response = self.client.post(self.send_new_email_verification_code_url, data=data)
        assert response.status_code == 200
        assert "Verification code sent successfully. Please check your mail" in response.data.get('message')

    def test_send_new_email_verification_code_existing_user(self):
        self._authenticate_with_tokens()
        user = self.user.objects.get()
        data = {"email": user.email}

        response = self.client.post(self.send_new_email_verification_code_url, data=data)
        assert response.status_code == 409
        assert "Account with this email already exists" in response.data.get('message')

    def test_logout_success_and_token_error(self):
        self._authenticate_with_tokens()

        data = {'refresh': self.tokens.get('refresh')}

        response = self.client.post(self.logout_url, data=data)
        assert response.status_code == 200
        assert 'Logged out successfully' in response.data.get('message')

        # Test with invalid token
        response = self.client.post(self.logout_url, data=data)
        assert response.status_code == 400
        assert 'Token is blacklisted' in response.data.get('message')

    def test_refresh_token(self):
        self._authenticate_with_tokens()

        data = {'refresh': self.tokens.get('refresh')}

        response = self.client.post(self.refresh_token_url, data=data)
        assert response.status_code == 200
        assert 'Refreshed successfully' in response.data.get('message')

    def test_request_forgot_password_code_success_and_non_existent_error(self):
        self._authenticate_with_tokens()
        user = self.user.objects.get()
        data = {"email": user.email}

        response = self.client.post(self.request_forgotten_password_code_url, data=data)
        assert response.status_code == 200
        assert "Password code sent successfully" in response.data.get('message')

        # Test with non-existent user
        data = {"email": "nonexistent@example.com"}
        response = self.client.post(self.request_forgotten_password_code_url, data=data)
        assert response.status_code == 404
        assert "Account not found" in response.data.get('message')

    def test_change_forgotten_password(self):
        # setting the self.encrypted_password_token
        self._verify_forgot_password_code()
        data = {"password": "new_password"}

        # Use reverse to generate the URL with the token included in the path
        url = reverse_lazy('change-forgotten-password', kwargs={'token': self.encrypted_password_token})

        response = self.client.post(url, data=data, format='json')

        assert response.status_code == 202
        assert "Password updated successfully" in response.data.get('message')

    def test_change_password(self):
        self._authenticate_with_tokens()
        data = {"password": "new_password"}

        response = self.client.post(self.change_password_url, data=data)
        assert response.status_code == 202
        assert "Password updated successfully" in response.data.get('message')

    def test_retrieve_employee_profile(self):
        self._authenticate_with_tokens()
        response = self.client.get(self.employee_profile_methods_url)
        assert response.status_code == 200
        assert "Retrieved profile successfully" in response.data.get('message')

        # Test the error by deleting the employee profile
        employee_profile = self.user.objects.get().employee_profile
        employee_profile.delete()

        response = self.client.get(self.employee_profile_methods_url)
        assert response.status_code == 404
        assert "No profile found for this user" in response.data.get('message')

    def test_update_employee_profile(self):
        self._authenticate_with_tokens()
        data = {"first_name": "new_first_name"}

        response = self.client.patch(self.employee_profile_methods_url, data=data)
        assert response.status_code == 202
        assert "Updated profile successfully" in response.data.get('message')

    def test_delete_employee_account(self):
        self._authenticate_with_tokens()
        self.user.objects.get()
        response = self.client.delete(self.employee_profile_methods_url)
        assert response.status_code == 204
        assert "Account deleted successfully" in response.data.get('message')

    def test_retrieve_company_profile(self):
        self._authenticate_with_company_tokens()
        response = self.client.get(self.company_profile_methods_url)
        assert response.status_code == 200
        assert "Retrieved profile successfully" in response.data.get('message')

        # Test the error by deleting the employee profile
        company_profile = self.user.objects.get().company_profile
        company_profile.delete()

        response = self.client.get(self.company_profile_methods_url)
        assert response.status_code == 404
        assert "No profile found for this user" in response.data.get('message')

    def test_update_company_profile(self):
        self._authenticate_with_company_tokens()
        data = {"first_name": "new_first_name"}

        response = self.client.patch(self.company_profile_methods_url, data=data)
        assert response.status_code == 202
        assert "Updated profile successfully" in response.data.get('message')

    def test_delete_company_account(self):
        self._authenticate_with_company_tokens()
        self.user.objects.get()
        response = self.client.delete(self.company_profile_methods_url)
        assert response.status_code == 204
        assert "Account deleted successfully" in response.data.get('message')
