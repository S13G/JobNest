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
from apps.common.permissions import IsAuthenticatedEmployee
from apps.common.responses import CustomResponse
from apps.jobs.choices import STATUS_PENDING, STATUS_ACCEPTED
from apps.jobs.filters import JobFilter
from apps.jobs.models import Job, JobType, AppliedJob
from apps.misc.models import Tip


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
        tags=['Home'],
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
                Q(recruiter__company_profile__name__icontains=search)).order_by('-created')

            data = [
                {
                    "id": single_job.id,
                    "title": single_job.title,
                    "recruiter": single_job.recruiter.company_profile.name,
                    "recruiter_image": single_job.recruiter.profile_image_url,
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
        tags=["Home"],
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
        queryset = Job.objects.all().order_by('-created')
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
                    "recruiter_image": job.recruiter.profile_image_url,
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
                response="Successfully retrieved successfully"
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
            # job_url = request.build.absolute_uri(job.get_absolute_url())
            data = {
                "id": job.id,
                "title": job.title,
                "recruiter": job.recruiter.company_profile.name,
                "recruiter_image": job.recruiter.profile_image_url,
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
            return CustomResponse.success(message="Successfully retrieved job", data=data)
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
        return CustomResponse.success(message="Successfully applied for job", data=None)


