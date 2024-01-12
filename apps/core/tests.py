import json

import pytest
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from rest_framework.test import APIClient

from apps.core.models import EmployeeProfile


class TestYourAppEndpoints(pytest.DjangoTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = APIClient()

    def test_employee_registration_success(self):
        # Test successful registration
        data = {
            'email': 'test@example.com',
            'password': 'test_password',
        }

        response = self.client.post(reverse_lazy('employee-registration'), data=json.dumps(data),
                                    content_type='application/json')
        assert response.status_code == 201
        assert 'Registration successful' in response.data.get('message', '')

    def test_employee_registration_conflict(self):
        # Test registration with existing user
        existing_user = User.objects.create_user(email='existing@example.com', password='existing_password')
        EmployeeProfile.objects.create(user=existing_user)  # Existing user with an employee profile

        data = {
            'email': 'existing@example.com',
            'password': 'new_password',
            # Add other required fields as needed
        }

        response = self.client.post(reverse_lazy('employee-registration'), data=json.dumps(data),
                                    content_type='application/json')
        assert response.status_code == 409
        assert 'Account already exists' in response.data.get('message', '')
