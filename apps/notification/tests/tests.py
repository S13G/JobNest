from django.contrib.auth import get_user_model
from django.urls import reverse_lazy

from apps.common.tests.tests import AuthTestCase

User = get_user_model()


class NotificationTestCase(AuthTestCase):

    def setUp(self):
        super().setUp()
        self.notification_url = reverse_lazy('retrieve-all-notifications')

    def test_get_employee_notifications(self):
        self._authenticate_with_tokens()
        response = self.client.get(self.notification_url)
        assert response.status_code == 200

    def test_get_company_notifications(self):
        self._authenticate_with_company_tokens()
        response = self.client.get(self.notification_url)
        assert response.status_code == 200
