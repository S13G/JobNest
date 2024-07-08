import pyotp
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy, reverse
from rest_framework.test import APITestCase


class AuthTestCase(APITestCase):

    def setUp(self):
        self.user = get_user_model()

        self.employee_data = {
            'email': 'test@example.com',
            'password': 'Testpassword#1234',
        }

        self.recruiter_data = {
            'email': 'testrecruiter@example.com',
            'password': 'Testpassword#1234',
        }

        self.tokens = ''

        # Store URLs in variables
        self.employee_registration_url = reverse_lazy('employee-registration')
        self.company_registration_url = reverse_lazy('company-registration')
        self.login_url = reverse_lazy('login')
        self.refresh_token_url = reverse_lazy('refresh-token')
        self.home_url = reverse_lazy('jobs-home')

    def _employee_registration_success(self):
        # Test successful registration
        response = self.client.post(self.employee_registration_url, data=self.employee_data)
        self.assertEqual(response.status_code, 201)
        otp_secret = response.data.get('data').get('secret')

        employee = self.user.objects.get(email=self.employee_data.get('email'))
        return employee, otp_secret

    def _company_registration_success(self):
        # Test successful registration
        response = self.client.post(self.company_registration_url, data=self.recruiter_data)
        self.assertEqual(response.status_code, 201)
        otp_secret = response.data.get('data').get('secret')

        company = self.user.objects.get(email=self.recruiter_data.get('email'))
        return company, otp_secret

    def _email_verification_success(self):
        # Using employee for the verification process since it's similar to the company
        employee, otp_secret = self._employee_registration_success()

        # Generate the OTP using the secret
        totp = pyotp.TOTP(s=otp_secret, interval=300, digits=4)
        otp = totp.now()

        user_data = {'email': employee.email, 'otp': otp}

        verify_email_url = reverse('verify-email', kwargs={'otp_secret': otp_secret})

        response = self.client.post(verify_email_url, data=user_data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Email verification successful', response.data.get('message'))

        return employee

    def _company_email_verification_success(self):
        # Using company for the verification process
        company, otp_secret = self._company_registration_success()

        # Generate the OTP using the secret
        totp = pyotp.TOTP(s=otp_secret, interval=300, digits=4)
        otp = totp.now()

        user_data = {'email': company.email, 'otp': otp}

        verify_email_url = reverse('verify-email', kwargs={'otp_secret': otp_secret})

        response = self.client.post(verify_email_url, data=user_data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Email verification successful', response.data.get('message'))

        return company

    def _login_success(self):
        # Test with registered employee profile
        employee = self._email_verification_success()

        response = self.client.post(self.login_url, data=self.employee_data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Logged in successfully', response.data.get('message'))
        self.assertIn('tokens', response.data.get('data'))
        self.assertIn('profile_data', response.data.get('data'))

        tokens = response.data.get('data').get('tokens')
        profile_data = response.data.get('data').get('profile_data')
        return tokens, profile_data

    def _company_login_success(self):
        # Test with registered company profile
        company = self._company_email_verification_success()

        response = self.client.post(self.login_url, data=self.recruiter_data)

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
