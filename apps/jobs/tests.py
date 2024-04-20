import json
import random

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse_lazy, reverse

from apps.common.tests import AuthTestCase
from apps.core.models import CompanyProfile
from apps.jobs.models import Job, JobType

User = get_user_model()


class JobsTestCase(AuthTestCase):

    def setUp(self):
        super().setUp()

        self.recruiter = User.objects.create_user(**self.recruiter_data, company=True, is_active=True,
                                                  email_verified=True)
        CompanyProfile.objects.create(user=self.recruiter, name='Test Company', country='US')

        with open('apps/jobs/test_data.json', 'r') as f:
            job_types_data = json.load(f)['job_types_data']

        JobType.objects.bulk_create([JobType(name=name) for name in job_types_data])

        self.job_types = JobType.objects.all()

        # read data from json file
        with open('apps/jobs/test_data.json', 'r') as f:
            jobs_data = json.load(f)['jobs_data']

        for job_data in jobs_data:
            random_job_type = random.choice(self.job_types)  # Select a random job type
            Job.objects.create(recruiter=self.recruiter, type=random_job_type, **job_data)

        self.jobs = Job.objects.all()

        # Store URLs in variables
        self.home_url = reverse_lazy('jobs-home')

    def test_home_view(self):
        self._authenticate_with_tokens()

        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)

        # adding 'type' query parameter to filter results
        response = self.client.get(self.home_url, {'type': '', 'location': 'Los Angeles'})
        self.assertEqual(response.status_code, 200)

    def test_get_specific_details_with_employee_login(self):
        self._authenticate_with_tokens()

        single_job = self.jobs.first()
        retrieve_single_job_url = reverse('job-details', kwargs={'id': single_job.id})
        response = self.client.get(retrieve_single_job_url, format='json')
        self.assertEqual(response.status_code, 200)

    def test_apply_job(self):
        self._authenticate_with_tokens()

        # Create a temporary test file
        file_content = b'test content'
        file_name = 'test.pdf'
        test_file = SimpleUploadedFile(file_name, file_content)

        self.data = {
            'cv': test_file  # Pass the test file as part of the data payload
        }

        single_job = self.jobs.first()
        apply_job_url = reverse('job-apply', kwargs={'id': single_job.id})
        response = self.client.post(apply_job_url, data=self.data)
        self.assertEqual(response.status_code, 200)



