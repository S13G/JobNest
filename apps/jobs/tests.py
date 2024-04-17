import json

from django.contrib.auth import get_user_model
from django.urls import reverse_lazy

from apps.common.tests import AuthTestCase
from apps.jobs.models import Job, JobType

User = get_user_model()


class JobsTestCase(AuthTestCase):

    def setUp(self):
        super().setUp()

        self.recruiter_data = {
            'email': 'testrecruiter@example.com',
            'password': 'testpassword',
        }

        with open('apps/jobs/test_data.json', 'r') as f:
            self.job_types_data = json.load(f)['job_types_data']

        self.job_types = JobType.objects.bulk_create([JobType(name=name) for name in self.job_types_data])

        self.recruiter = User.objects.create_user(**self.recruiter_data, is_active=True, company=True)

        # read data from json file
        with open('apps/jobs/test_data.json', 'r') as f:
            self.jobs_data = json.load(f)['jobs_data']

        # Create database objects from supplied data
        self.jobs = Job.objects.bulk_create([
            Job(recruiter=self.recruiter, type=self.job_types[0], **job_data) for job_data in self.jobs_data
        ])

        # Store URLs in variables
        self.home_url = reverse_lazy('jobs-home')

    def test_home_view(self):
        self._authenticate_with_tokens()

        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)

        # adding 'type' query parameter to filter results
        response = self.client.get(self.home_url, {'type': 'FULL_TIME'})
        self.assertEqual(response.status_code, 200)
