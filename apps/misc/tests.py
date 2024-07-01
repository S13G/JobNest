from django.contrib.auth import get_user_model
from django.urls import reverse_lazy, reverse

from apps.common.tests import AuthTestCase
from apps.misc.models import Tip

User = get_user_model()


# Create your websocket_test here.
class MiscTestCase(AuthTestCase):

    def setUp(self):
        super().setUp()

        # URLs
        self.refresh_token_url = reverse_lazy('refresh-token')
        self.retrieve_all_tips = reverse_lazy('retrieve-all-tips')
        self.retrieve_single_tip = reverse_lazy('retrieve-tip')
        self.filter_faqs = reverse_lazy('filter-all-faqs')
        self.retrieve_faq_types = reverse_lazy('retrieve-all-faqs-types')

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
