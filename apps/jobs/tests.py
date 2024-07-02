import json
import random
import uuid
from io import BytesIO

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse_lazy, reverse

from apps.common.tests import AuthTestCase
from apps.core.models import CompanyProfile, EmployeeProfile
from apps.jobs.models import Job, JobType, AppliedJob, SavedJob

User = get_user_model()


class JobsTestCase(AuthTestCase):

    def setUp(self):
        super().setUp()

        # Using a new recruiter data to avoid conflicts with other test cases
        self.new_recruiter_data = {
            'email': 'testrecruiter2@example.com',
            'password': 'testpassword',
        }

        self.new_recruiter = User.objects.create_user(**self.new_recruiter_data, company=True, 
                                                      email_verified=True)

        # Creating a company profile for the new recruiter
        CompanyProfile.objects.create(user=self.new_recruiter, name='Test Company', country='US')

        with open('apps/jobs/test_data.json', 'r') as f:
            job_types_data = json.load(f)['job_types_data']

        JobType.objects.bulk_create([JobType(name=name) for name in job_types_data])

        self.job_types = JobType.objects.all()

        # read data from json file
        with open('apps/jobs/test_data.json', 'r') as f:
            jobs_data = json.load(f)['jobs_data']

        for job_data in jobs_data:
            random_job_type = random.choice(self.job_types)  # Select a random job type
            Job.objects.create(recruiter=self.new_recruiter, type=random_job_type, **job_data)

        self.jobs = Job.objects.all()

        self.created_job = None

        # Store URLs in variables
        self.home_url = reverse_lazy('jobs-home')
        self.search_applied_jobs_url = reverse_lazy('applied-jobs-search')
        self.filter_applied_jobs_url = reverse_lazy('filter-applied-jobs')
        self.saved_jobs_url = reverse_lazy('saved-jobs')
        self.search_vacancies_url = reverse_lazy('search-vacancies')
        self.vacancies_home_url = reverse_lazy('filter-vacancies')
        self.job_types_url = reverse_lazy('job-types-all')
        self.create_job_vacancy_url = reverse_lazy('create-job')

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

        data = {
            'cv': test_file  # Pass the test file as part of the data payload
        }

        single_job = self.jobs.first()
        apply_job_url = reverse('job-apply', kwargs={'id': single_job.id})
        response = self.client.post(apply_job_url, data=data)
        self.assertEqual(response.status_code, 200)

        # checking if user has already applied for the job and either the status is accepted or pending
        # Create a new temporary test file
        file_content = b'test content 2'
        file_name = 'test2.pdf'
        test_file = SimpleUploadedFile(file_name, file_content)

        new_data = {
            'cv': test_file  # Pass the test file as part of the data payload
        }
        response = self.client.post(apply_job_url, data=new_data)
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

        # checking if job has been deleted and doesn't exist
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

        search_query = 'marketing'  # Replace with your search query
        query_params = {'search': search_query}
        response = self.client.get(self.search_vacancies_url, data=query_params)
        self.assertEqual(response.status_code, 200)

    def test_vacancies_home(self):
        self._authenticate_with_company_tokens()

        bool_query = False
        query_param = {'active': bool_query}
        response = self.client.get(self.vacancies_home_url, data=query_param)
        self.assertEqual(response.status_code, 200)

    def test_retrieve_all_job_types(self):
        self._authenticate_with_company_tokens()

        response = self.client.get(self.job_types_url)
        self.assertEqual(response.status_code, 200)

    def _create_job_vacancy(self):
        self._authenticate_with_company_tokens()

        # Create a new temporary image
        image = Image.new('RGB', (100, 100))  # Create a 100x100 pixel image
        file_name = 'test_image.png'
        tmp_file = BytesIO()  # Create a temporary file object
        image.save(tmp_file, 'png')  # Save the image to the temporary file
        tmp_file.seek(0)  # Reset the file pointer to the beginning

        job_type = JobType.objects.first()

        new_data = {
            'image': SimpleUploadedFile(file_name, tmp_file.read()),  # Pass the test image as part of the data payload,
            'title': 'Test Job',
            'salary': 1000.00,
            'location': 'GB',
            'type': str(job_type.id),
            'requirements': ['Requirement 1', 'Requirement 2'],
        }

        response = self.client.post(self.create_job_vacancy_url, data=new_data)

        # Reassigning a new value to the instance variable
        self.created_job = Job.objects.get(id=response.data.get('data').get('id'))
        self.assertEqual(response.status_code, 201)

    def test_create_update_delete_job_vacancy(self):
        self._create_job_vacancy()

        # Update a job vacancy
        update_job_vacancy_url = reverse('update-delete-job', kwargs={'id': self.created_job.id})

        job_type = JobType.objects.first()

        updated_data = {
            'title': 'Updated Test Job',
            'salary': 1000.00,
            'location': 'PT',
            'type': str(job_type.id),
            'requirements': ['Requirement 3', 'Requirement 2'],
        }
        updated_response = self.client.patch(update_job_vacancy_url, data=updated_data)
        self.assertEqual(updated_response.status_code, 202)

        # Delete a job
        delete_job_vacancy_url = reverse('update-delete-job', kwargs={'id': self.created_job.id})
        response = self.client.delete(delete_job_vacancy_url)
        self.assertEqual(response.status_code, 204)

        # Job doesn't exist to be deleted
        invalid_id = uuid.uuid4()
        invalid_delete_job_vacancy_url = reverse('update-delete-job', kwargs={'id': invalid_id})
        response = self.client.delete(invalid_delete_job_vacancy_url)
        self.assertEqual(response.status_code, 404)

    def test_update_applied_job(self):
        self._create_job_vacancy()

        # Simulating the user applying for a job
        file_content = b'test content'
        file_name = 'test.pdf'
        test_file = SimpleUploadedFile(file_name, file_content)

        created_applicant = self.user.objects.create_user(**self.employee_data,  email_verified=True)

        # Create employee profile for applicant
        data = {
            'full_name': 'John Doe',
            'date_of_birth': '1990-01-01',
            'address': '123 Main St',
            'occupation': 'Software Engineer'
        }
        EmployeeProfile.objects.create(user=created_applicant, **data)

        created_applied_job = AppliedJob.objects.create(cv=test_file, job=self.created_job, user=created_applicant)
        applied_job_id = created_applied_job.id
        # getting the applied job id
        update_applied_job_url = reverse('update-applied-job', kwargs={'id': applied_job_id})

        # updating the applied job
        updated_data = {
            'review': 'You\'re a wonderful candidate',
            'status': 'ACCEPTED'
        }

        response = self.client.patch(update_applied_job_url, data=updated_data)
        self.assertEqual(response.status_code, 202)

        # Job doesn't exist to be deleted
        invalid_id = uuid.uuid4()
        invalid_delete_job_vacancy_url = reverse('update-applied-job', kwargs={'id': invalid_id})
        response = self.client.patch(invalid_delete_job_vacancy_url, data=updated_data)
        self.assertEqual(response.status_code, 404)
