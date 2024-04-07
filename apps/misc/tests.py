import pyotp
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy, reverse
from faker import Faker
from rest_framework.test import APITestCase, APIClient

from apps.core.models import OTPSecret
from apps.misc.models import Tip

User = get_user_model()


# Create your websocket_test here.
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

        # Store URLs in variables
        self.employee_registration_url = reverse_lazy('employee-registration')
        self.company_registration_url = reverse_lazy('company-registration')
        self.verify_email_url = reverse_lazy('verify-email')
        self.login_url = reverse_lazy('login')
        self.refresh_token_url = reverse_lazy('refresh-token')
        self.retrieve_all_tips = reverse_lazy('retrieve-all-tips')
        self.retrieve_single_tip = reverse_lazy('retrieve-tip')
        self.filter_faqs = reverse_lazy('filter-all-faqs')
        self.retrieve_faq_types = reverse_lazy('retrieve-all-faqs-types')

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

    def test_retrieve_all_tips(self):
        self._authenticate_with_tokens()
        response = self.client.get(self.retrieve_all_tips)
        self.assertEqual(response.status_code, 200)

    def test_retrieve_single_tip(self):
        self._authenticate_with_tokens()
        # Create a new tip object
        tip = Tip.objects.create(title='New tip', description='This is a new tip', author="John Doe")
        new_tip_id = tip.id
        # Use reverse when you are passing arguments
        retrieve_single_tip_url = reverse('retrieve-tip', kwargs={'tip_id': new_tip_id})
        response = self.client.get(retrieve_single_tip_url, format='json')
        self.assertEqual(response.status_code, 200)

    def test_filter_faqs(self):
        self._authenticate_with_tokens()
        response = self.client.get(self.filter_faqs)
        self.assertEqual(response.status_code, 200)

    def test_retrieve_faq_types(self):
        self._authenticate_with_tokens()
        response = self.client.get(self.retrieve_faq_types)
        self.assertEqual(response.status_code, 200)
