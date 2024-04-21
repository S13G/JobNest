import json
import random
import uuid

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse_lazy, reverse

from apps.common.tests import AuthTestCase
from apps.core.models import CompanyProfile
from apps.jobs.models import Job, JobType, AppliedJob, SavedJob

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
        self.search_applied_jobs_url = reverse_lazy('applied-jobs-search')
        self.filter_applied_jobs_url = reverse_lazy('filter-applied-jobs')
        self.saved_jobs_url = reverse_lazy('saved-jobs')
        self.search_vacancies_url = reverse_lazy('search-vacancies')

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

        # checking if user has already applied for the job and either the status is accepted or pending
        # Create a new temporary test file
        file_content = b'test content 2'
        file_name = 'test2.pdf'
        test_file = SimpleUploadedFile(file_name, file_content)

        self.new_data = {
            'cv': test_file  # Pass the test file as part of the data payload
        }
        response = self.client.post(apply_job_url, data=self.new_data)
        self.assertEqual(response.status_code, 409)

    def test_search_applied_jobs(self):
        self.test_apply_job()  # Get the applied job

        search_query = 'test'  # Replace with your search query
        query_params = {'search': search_query}

        response = self.client.get(self.search_applied_jobs_url, data=query_params)
        self.assertEqual(response.status_code, 200)

    def test_get_applied_job_details(self):
        self.test_apply_job()  # Get the applied job

        applied_job = AppliedJob.objects.first()
        retrieve_applied_job_url = reverse('applied-job-details', kwargs={'id': applied_job.id})
        response = self.client.get(retrieve_applied_job_url, format='json')
        self.assertEqual(response.status_code, 200)

        # testing for invalid id
        invalid_id = uuid.uuid4()
        invalid_applied_job_url = reverse('applied-job-details', kwargs={'id': invalid_id})
        response = self.client.get(invalid_applied_job_url, format='json')
        self.assertEqual(response.status_code, 404)

    def test_filter_applied_jobs(self):
        self.test_apply_job()  # Get the applied job

        search_query = 'PENDING'
        query_params = {'status': search_query}

        response = self.client.get(self.filter_applied_jobs_url, data=query_params)
        self.assertEqual(response.status_code, 200)

    def test_create_delete_saved_jobs(self):
        self._authenticate_with_tokens()

        single_job = self.jobs.first()
        save_job_url = reverse('create-delete-saved-job', kwargs={'id': single_job.id})
        response = self.client.post(save_job_url)
        self.assertEqual(response.status_code, 200)

        # checking for conflict (if job has already been saved)
        response = self.client.post(save_job_url)
        self.assertEqual(response.status_code, 409)

        # delete job
        saved_job = SavedJob.objects.first()
        delete_saved_job_url = reverse('create-delete-saved-job', kwargs={'id': saved_job.id})
        response = self.client.delete(delete_saved_job_url)
        self.assertEqual(response.status_code, 204)

        # checking if job has been deleted and doesnt exist
        response = self.client.delete(delete_saved_job_url)
        self.assertEqual(response.status_code, 404)

    def test_retrieve_all_saved_jobs(self):
        self._authenticate_with_tokens()

        response = self.client.get(self.saved_jobs_url)
        self.assertEqual(response.status_code, 200)

    """
    COMPANY SECTION
    """

    def test_search_vacancies(self):
        self._authenticate_with_company_tokens()

        search_query = 'test'  # Replace with your search query
        query_params = {'search': search_query}
        response = self.client.get(self.search_vacancies_url, data=query_params)
        self.assertEqual(response.status_code, 200)
