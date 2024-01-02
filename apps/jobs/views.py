import pycountry
from django.db import transaction
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from rest_framework import status
from rest_framework.views import APIView

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.permissions import IsAuthenticatedEmployee, IsAuthenticatedCompany
from apps.common.responses import CustomResponse
from apps.jobs.choices import STATUS_PENDING, STATUS_ACCEPTED
from apps.jobs.filters import JobFilter, AppliedJobFilter, VacanciesFilter
from apps.jobs.models import Job, JobType, AppliedJob, SavedJob
from apps.jobs.serializers import CreateJobSerializer
from apps.misc.models import Tip
from apps.notification.choices import NOTIFICATION_JOB_APPLIED
from apps.notification.models import Notification


# # Create your views here.

class SearchJobsView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @extend_schema(
        summary="Search jobs",
        parameters=[
            OpenApiParameter(name="search", type=OpenApiTypes.STR, required=False)
        ],
        description=(
                "This endpoint allows an authenticated job seeker to search for jobs"
        ),
        tags=['Job Seeker Home'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved searched jobs",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="No jobs found",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Missing required parameters",
            )
        }
    )
    def get(self, request, *args, **kwargs):
        search = self.request.query_params.get('search', None)

        if search is None:
            raise RequestError(err_code=ErrorCode.INVALID_ENTRY, err_msg="Missing required parameters", data={},
                               status_code=status.HTTP_400_BAD_REQUEST)

        try:
            jobs = Job.objects.filter(
                Q(title__icontains=search) |
                Q(location__icontains=search) | Q(type__name__icontains=search) |
                Q(recruiter__company_profile__name__icontains=search), active=True).order_by('-created')

            data = [
                {
                    "id": single_job.id,
                    "title": single_job.title,
                    "recruiter": single_job.recruiter.company_profile.name,
                    "job_image": single_job.image_url,
                    "location": single_job.location,
                    "type": single_job.type.name,
                    "salary": single_job.salary,
                    "is_saved": single_job.is_saved_by_user(request.user),
                }
                for single_job in jobs
            ]
            return CustomResponse.success(message="Successfully retrieved searched jobs", data=data)

        except Job.DoesNotExist:
            return CustomResponse.success(message="No jobs found", data=None)


class JobsHomeView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = JobFilter

    @extend_schema(
        summary="Get home page",
        description=(
                """
                Get home page: Search, Retrieve all job types, and all jobs and also tip including notifications.
                """
        ),
        parameters=[
            OpenApiParameter('type', type=OpenApiTypes.STR, required=False, description="Filter jobs by type"),
            OpenApiParameter('location', type=OpenApiTypes.STR, required=False, description="Filter jobs by location"),
            OpenApiParameter('salary', type=OpenApiTypes.STR, required=False, description="Filter jobs by salary"),
        ],
        tags=["Job Seeker Home"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response="Retrieved successfully"
            )
        }
    )
    def get(self, request):
        profile_name = request.user.employee_profile.full_name
        tip = Tip.objects.only('title').order_by('-created').first()
        job_types = JobType.objects.only('name')
        queryset = Job.objects.filter(active=True).order_by('-created')
        queryset = self.filterset_class(data=request.GET, queryset=queryset).qs
        data = {
            "profile_name": profile_name,
            "tip": {
                "id": tip.id,
                "title": tip.title,
                "author_image": tip.author_image_url
            },
            "job_types": [
                {
                    "id": job_type.id,
                    "name": job_type.name
                }
                for job_type in job_types
            ],
            "jobs": [
                {
                    "id": job.id,
                    "title": job.title,
                    "recruiter": job.recruiter.company_profile.name,
                    "job_image": job.image_url,
                    "location": job.location,
                    "type": job.type.name,
                    "salary": job.salary,
                    "is_saved": job.is_saved_by_user(request.user)
                }
                for job in queryset
            ]
        }
        return CustomResponse.success(message="Retrieved successfully", data=data)


class JobDetailsView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @extend_schema(
        summary="Get single job",
        description=(
                """
                Get single job: Retrieve a single job
                """
        ),
        tags=["Job"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response="Successfully retrieved job details"
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Job with this id does not exist",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Missing required parameters",
            )
        }
    )
    def get(self, request, *args, **kwargs):
        job_id = self.kwargs.get('id', None)

        if job_id is None:
            raise RequestError(ErrorCode.INVALID_ENTRY, err_msg="Missing required parameters", data={},
                               status_code=status.HTTP_400_BAD_REQUEST)

        try:
            job = Job.objects.get(id=job_id)
            data = {
                "id": job.id,
                "title": job.title,
                "recruiter": job.recruiter.company_profile.name,
                "job_image": job.image_url,
                "location": pycountry.countries.get(alpha_2=job.location).name,
                "type": job.type.name,
                "salary": job.salary,
                "is_saved": job.is_saved_by_user(request.user),
                "requirements": [
                    {
                        "id": requirement.id,
                        "requirement": requirement.requirement
                    }
                    for requirement in job.requirements.all()
                ],
                "url": job.get_absolute_url()
            }
            return CustomResponse.success(message="Successfully retrieved job details", data=data)
        except Job.DoesNotExist:
            return CustomResponse.success(message="Job with this id does not exist", data=None,
                                          status_code=status.HTTP_404_NOT_FOUND)


class JobApplyView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @extend_schema(
        summary="Apply for a job",
        description=(
                """
                This endpoint allows a authenticated user to apply for a job
                """
        ),
        tags=["Job"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response="Successfully applied for job"
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Job with this id does not exist",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Missing required parameters or upload a cv",
            ),
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: OpenApiResponse(
                description="Unsupported file type. Only PDF and DOC files are accepted.",
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                description="Internal server error",
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                description="Already applied for this job",
            )
        }
    )
    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        job_id = self.kwargs.get('id', None)
        cv = request.FILES.get('cv', None)

        if job_id is None:
            raise RequestError(err_code=ErrorCode.INVALID_ENTRY, err_msg="Missing required parameters", data={},
                               status_code=status.HTTP_400_BAD_REQUEST)

        if cv is None:
            raise RequestError(err_code=ErrorCode.OTHER_ERROR, err_msg="Upload a cv", data={},
                               status_code=status.HTTP_400_BAD_REQUEST)

        # Check if the uploaded file is a PDF or DOC
        valid_extensions = ['pdf', 'doc', 'docx']
        file_extension = cv.name.split('.')[-1].lower()
        if file_extension not in valid_extensions:
            raise RequestError(err_code=ErrorCode.OTHER_ERROR,
                               err_msg="Unsupported file type. Only PDF and DOC files are accepted.",
                               status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

        job = Job.objects.get(id=job_id)  # Try to get the job

        if job is None:
            raise RequestError(err_code=ErrorCode.INVALID_ENTRY, err_msg="Job with this id does not exist", data={},
                               status_code=status.HTTP_404_NOT_FOUND)

        # Check if the user has already applied to the job and their application is still pending
        existing_pending_application = AppliedJob.objects.filter(job=job, user=request.user,
                                                                 status=STATUS_PENDING).exists()
        if existing_pending_application:
            raise RequestError(err_code=ErrorCode.INVALID_ENTRY,
                               err_msg="You have already applied to this job and your application is still pending.",
                               data={}, status_code=status.HTTP_409_CONFLICT)

        # Check if the user has already applied to the job and their application has been accepted
        existing_accepted_application = AppliedJob.objects.filter(job=job, user=request.user,
                                                                  status=STATUS_ACCEPTED).exists()
        if existing_accepted_application:
            raise RequestError(err_code=ErrorCode.INVALID_ENTRY,
                               err_msg="You have already applied to this job and your application has been accepted.",
                               data={}, status_code=status.HTTP_409_CONFLICT)

        AppliedJob.objects.create(job=job, cv=cv, user=request.user)  # create the applied job

        Notification.objects.create(user=request.user, notification_type=NOTIFICATION_JOB_APPLIED,
                                    message="You have applied for a job")

        return CustomResponse.success(message="Successfully applied for job", data=None)


class AppliedJobsSearchView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @extend_schema(
        summary="Search applied jobs",
        parameters=[
            OpenApiParameter(name="search", type=OpenApiTypes.STR, required=False)
        ],
        description=(
                "This endpoint allows an authenticated job seeker to search for their applied jobs"
        ),
        tags=['Job'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved searched applied jobs",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="No applied jobs found",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Missing required parameters",
            )
        }
    )
    def get(self, request, *args, **kwargs):
        search = self.request.query_params.get('search', None)

        if search is None:
            raise RequestError(err_code=ErrorCode.INVALID_ENTRY, err_msg="Missing required parameters", data={},
                               status_code=status.HTTP_400_BAD_REQUEST)

        try:
            applied_jobs = AppliedJob.objects.filter(
                Q(job__title__icontains=search) |
                Q(job__location__icontains=search) | Q(job__type__name__icontains=search) |
                Q(job__recruiter__company_profile__name__icontains=search) |
                Q(status__icontains=search)).order_by('-created')

            data = [
                {
                    "id": single_job.id,
                    "title": single_job.job.title,
                    "recruiter": single_job.job.recruiter.company_profile.name,
                    "job_image": single_job.image_url,
                    "status": single_job.status,
                }
                for single_job in applied_jobs
            ]
            return CustomResponse.success(message="Successfully retrieved searched applied jobs", data=data)

        except AppliedJob.DoesNotExist:
            return CustomResponse.success(message="No applied jobs found", data=None)


class AppliedJobDetailsView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @extend_schema(
        summary="Get applied job details",
        description=(
                """
                Get single applied job: Retrieve the details of the applied job, pass in the `id` of the applied job to the path parameter.
                """
        ),
        tags=["Job"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response="Successfully retrieved job details",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Applied job with this id does not exist",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Missing required parameters",
            )
        }
    )
    def get(self, request, *args, **kwargs):
        applied_job_id = self.kwargs.get('id', None)

        if applied_job_id is None:
            raise RequestError(ErrorCode.INVALID_ENTRY, err_msg="Missing required parameters", data={},
                               status_code=status.HTTP_400_BAD_REQUEST)

        try:
            applied_job = AppliedJob.objects.get(id=applied_job_id)

            data = {
                "id": applied_job.id,
                "title": applied_job.job.title,
                "recruiter": applied_job.job.recruiter.company_profile.name,
                "job_image": applied_job.job.image_url,
                "location": pycountry.countries.get(alpha_2=applied_job.job.location).name,
                "type": applied_job.job.type.name,
                "salary": applied_job.job.salary,
                "status": applied_job.status,
                "review": applied_job.review,
            }
            return CustomResponse.success(message="Successfully retrieved job details", data=data)
        except AppliedJob.DoesNotExist:
            return CustomResponse.success(message="Applied job with this id does not exist", data=None,
                                          status_code=status.HTTP_404_NOT_FOUND)


class FilterAppliedJobsView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = AppliedJobFilter

    @extend_schema(
        summary="Get all applications and filter",
        description=(
                """
                This endpoint gets all applications the authenticated user has applied to with some filters option
                """
        ),
        parameters=[
            OpenApiParameter('status', type=OpenApiTypes.STR, required=False, description="Filter jobs by type"),
        ],
        tags=["Job"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response="Retrieved successfully"
            )
        }
    )
    def get(self, request):
        queryset = AppliedJob.objects.all().order_by('-created')
        queryset = self.filterset_class(data=request.GET, queryset=queryset).qs
        data = {
            "applications": [
                {
                    "id": application.id,
                    "title": application.job.title,
                    "recruiter": application.job.recruiter.company_profile.name,
                    "job_image": application.job.image_url,
                    "status": application.status,
                    "salary": application.salary,
                    "type": application.type.name,
                    "location": application.job.location,
                    "review": application.review
                }
                for application in queryset
            ]
        }
        return CustomResponse.success(message="Retrieved successfully", data=data)


class CreateDeleteSavedJobsView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @extend_schema(
        summary="Create saved job",
        description=(
                """
                Create saved job: Create a saved job, pass in the `id` of the job to the path parameter.
                """
        ),
        tags=["Job"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response="Successfully created saved job",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Job with this id does not exist",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Missing required parameters",
            )
        }
    )
    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        job_id = self.kwargs.get('id', None)

        if job_id is None:
            raise RequestError(ErrorCode.INVALID_ENTRY, err_msg="Missing required parameters", data={},
                               status_code=status.HTTP_400_BAD_REQUEST)

        job = Job.objects.get(id=job_id)
        if job is None:
            raise RequestError(ErrorCode.INVALID_ENTRY, err_msg="Job with this id does not exist", data={},
                               status_code=status.HTTP_404_NOT_FOUND)

        if job.is_saved_by_user(request.user):
            raise RequestError(ErrorCode.INVALID_ENTRY, err_msg="Job is already saved", data={},
                               status_code=status.HTTP_400_BAD_REQUEST)

        saved_job = SavedJob.objects.create(job=job, user=request.user)
        data = {
            "id": saved_job.id,
            "job_id": saved_job.job.id,
            "title": saved_job.job.title,
            "recruiter": saved_job.job.recruiter.company_profile.name,
            "job_image": saved_job.job.image_url,
            "location": pycountry.countries.get(alpha_2=saved_job.job.location).name,
            "type": saved_job.job.type.name,
            "salary": saved_job.job.salary,
            "is_saved": saved_job.job.is_saved_by_user(request.user)
        }
        return CustomResponse.success(message="Successfully created saved job", data=data)

    @extend_schema(
        summary="Delete saved job",
        description=(
                """
                Delete saved job: Delete a saved job, pass in the `id` of the saved job to the path parameter.
                """
        ),
        tags=["Job"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response="Successfully deleted saved job",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Saved job with this id does not exist",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Missing required parameters",
            )
        }
    )
    def delete(self, request, *args, **kwargs):
        saved_job_id = self.kwargs.get('id', None)

        if saved_job_id is None:
            raise RequestError(ErrorCode.INVALID_ENTRY, err_msg="Missing required parameters", data={},
                               status_code=status.HTTP_400_BAD_REQUEST)

        saved_job = SavedJob.objects.get(id=saved_job_id, user=request.user)
        if saved_job is None:
            raise RequestError(ErrorCode.INVALID_ENTRY, err_msg="Saved job with this id does not exist", data={},
                               status_code=status.HTTP_404_NOT_FOUND)

        saved_job.delete()
        return CustomResponse.success(message="Successfully deleted saved job")


class RetrieveAllSavedJobsView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @extend_schema(
        summary="Get saved jobs",
        description=(
                """
                Get saved jobs: Get a list of saved jobs.
                `P.S`: Use the job id to get the details of the job using the job details endpoint.
                """
        ),
        tags=["Job"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response="Successfully retrieved saved jobs",
            ),
        }
    )
    def get(self, request):
        saved_jobs = SavedJob.objects.filter(user=request.user)
        data = {
            "saved_jobs": [
                {
                    "id": saved_job.id,
                    "job_id": saved_job.job.id,
                    "title": saved_job.job.title,
                    "recruiter": saved_job.job.recruiter.company_profile.name,
                    "job_image": saved_job.job.image_url,
                    "location": pycountry.countries.get(alpha_2=saved_job.job.location).name,
                    "type": saved_job.job.type.name,
                    "salary": saved_job.job.salary,
                    "is_saved": saved_job.job.is_saved_by_user(request.user)
                }
                for saved_job in saved_jobs
            ]
        }
        return CustomResponse.success(message="Successfully retrieved saved jobs", data=data)


class SearchVacanciesView(APIView):
    permission_classes = (IsAuthenticatedCompany,)

    @extend_schema(
        summary="Search jobs",
        parameters=[
            OpenApiParameter(name="search", type=OpenApiTypes.STR, required=False)
        ],
        description=(
                "This endpoint allows an authenticated job recruiter to search for his posted vacancies"
        ),
        tags=['Job Recruiter Home'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved posted vacancies",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="No vacancies found",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Missing required parameters",
            )
        }
    )
    def get(self, request, *args, **kwargs):
        search = self.request.query_params.get('search', None)

        if search is None:
            raise RequestError(err_code=ErrorCode.INVALID_ENTRY, err_msg="Missing required parameters", data={},
                               status_code=status.HTTP_400_BAD_REQUEST)

        try:
            jobs = Job.objects.filter(
                Q(title__icontains=search) |
                Q(location__icontains=search) | Q(type__name__icontains=search) |
                Q(recruiter__company_profile__name__icontains=search)).order_by('-created')

            data = [
                {
                    "id": single_job.id,
                    "title": single_job.title,
                    "recruiter": single_job.recruiter.company_profile.name,
                    "job_image": single_job.image_url,
                    "location": single_job.location,
                    "type": single_job.type.name,
                    "salary": single_job.salary,
                    "active": single_job.active,
                }
                for single_job in jobs
            ]
            return CustomResponse.success(message="Successfully retrieved searched vacancies", data=data)
        except Job.DoesNotExist:
            return CustomResponse.success(message="No jobs found", data=None)


class VacanciesHomeView(APIView):
    permission_classes = (IsAuthenticatedCompany,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = VacanciesFilter

    @extend_schema(
        summary="Get home page",
        description=(
                """
                Get home page: Search, Retrieve all job types, and all jobs and also tip including notifications.
                """
        ),
        parameters=[
            OpenApiParameter('active', type=OpenApiTypes.BOOL, required=False, description="Filter jobs by active"),
        ],
        tags=["Job Recruiter Home"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response="Retrieved successfully"
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Missing required parameters",
            ),
        }
    )
    def get(self, request):
        profile_name = request.user.company_profile.name
        my_vacancies = Job.objects.filter(recruiter=request.user).order_by('-created')
        all_applied_jobs = AppliedJob.objects.filter(job__recruiter=request.user).order_by('-created')
        queryset = self.filterset_class(data=request.GET, queryset=my_vacancies).qs

        data = {
            "profile_name": profile_name,
            "vacancies": [
                {
                    "id": job.id,
                    "title": job.title,
                    "recruiter": job.recruiter.company_profile.name,
                    "job_image": job.image_url,
                    "location": job.location,
                    "type": job.type.name,
                    "salary": job.salary,
                    "active": job.active
                }
                for job in queryset
            ],
            "all_applied_applicants": [
                {
                    "id": applied_job.id,
                    "full_name": applied_job.user.employee_profile.full_name,
                    "job_title": applied_job.job.title,
                    "cv": applied_job.cv.url
                }
                for applied_job in all_applied_jobs
            ]
        }
        return CustomResponse.success(message="Retrieved successfully", data=data)


class CreateVacanciesView(APIView):
    permission_classes = (IsAuthenticatedCompany,)

    @extend_schema(
        summary="Create a new job",
        description=(
                "This endpoint allows an authenticated job recruiter to create a new job"
        ),
        tags=['Job Recruiter Home'],
        request=CreateJobSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Successfully created a new job",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Missing required parameters",
            ),
        }
    )
    def post(self, request):
        pass
