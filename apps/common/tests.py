import pyotp
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from rest_framework.test import APITestCase

from apps.core.models import OTPSecret


class AuthTestCase(APITestCase):

    def setUp(self):
        self.user = get_user_model()

        self.employee_data = {
            'email': 'test@example.com',
            'password': 'test_password',
        }

        self.recruiter_data = {
            'email': 'testrecruiter@example.com',
            'password': 'testpassword',
        }

        self.tokens = ''

        # Store URLs in variables
        self.employee_registration_url = reverse_lazy('employee-registration')
        self.company_registration_url = reverse_lazy('company-registration')
        self.verify_email_url = reverse_lazy('verify-email')
        self.login_url = reverse_lazy('login')
        self.refresh_token_url = reverse_lazy('refresh-token')
        self.home_url = reverse_lazy('jobs-home')

    def _employee_registration_success(self):
        # Test successful registration
        response = self.client.post(self.employee_registration_url, data=self.employee_data)
        self.assertEqual(response.status_code, 201)

        employee = self.user.objects.get(email=self.employee_data.get('email'))
        return employee

    def _company_registration_success(self):
        # Test successful registration
        response = self.client.post(self.company_registration_url, data=self.recruiter_data)
        self.assertEqual(response.status_code, 201)

        company = self.user.objects.get(email=self.recruiter_data.get('email'))
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

        self.assertEqual(response.status_code, 200)
        self.assertIn('Email verification successful', response.data.get('message'))

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

        self.assertEqual(response.status_code, 200)
        self.assertIn('Email verification successful', response.data.get('message'))

        return company, otp_secret

    def _login_success(self):
        # Test with registered employee profile
        employee, _ = self._email_verification_success()

        user_data = {"email": employee.email, "password": 'test_password'}

        response = self.client.post(self.login_url, data=user_data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Logged in successfully', response.data.get('message'))
        self.assertIn('tokens', response.data.get('data'))
        self.assertIn('profile_data', response.data.get('data'))

        tokens = response.data.get('data').get('tokens')
        profile_data = response.data.get('data').get('profile_data')
        return tokens, profile_data

    def _company_login_success(self):
        # Test with registered company profile
        company, _ = self._company_email_verification_success()

        user_data = {"email": company.email, "password": 'testpassword'}

        response = self.client.post(self.login_url, data=user_data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Logged in successfully', response.data.get('message'))
        self.assertIn('tokens', response.data.get('data'))
        self.assertIn('profile_data', response.data.get('data'))

        tokens = response.data.get('data').get('tokens')
        profile_data = response.data.get('data').get('profile_data')
        return tokens, profile_data

    def _authenticate_with_tokens(self):
        tokens, _ = self._login_success()
        self.tokens = tokens
        self.client.force_authenticate(user=self.user.objects.get(email=self.employee_data.get('email')),
                                       token=tokens.get('access'))

    def _authenticate_with_company_tokens(self):
        tokens, _ = self._company_login_success()
        self.tokens = tokens
        self.client.force_authenticate(user=self.user.objects.get(email=self.recruiter_data.get('email')),
                                       token=tokens.get('access'))
