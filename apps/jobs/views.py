import pycountry
from django.db import transaction
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiExample
from rest_framework import status
from rest_framework.views import APIView

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.permissions import IsAuthenticatedEmployee, IsAuthenticatedCompany
from apps.common.responses import CustomResponse
from apps.jobs.choices import STATUS_PENDING, STATUS_ACCEPTED, STATUS_REJECTED, STATUS_SCHEDULED_FOR_INTERVIEW
from apps.jobs.filters import JobFilter, AppliedJobFilter, VacanciesFilter
from apps.jobs.models import Job, JobType, AppliedJob, SavedJob, JobRequirement
from apps.jobs.serializers import CreateJobSerializer, UpdateVacanciesSerializer, UpdateAppliedJobSerializer, \
    JobApplySerializer
from apps.misc.models import Tip
from apps.notification.choices import NOTIFICATION_JOB_APPLIED, NOTIFICATION_APPLICATION_ACCEPTED, \
    NOTIFICATION_APPLICATION_REJECTED, NOTIFICATION_APPLICATION_SCHEDULED_FOR_INTERVIEW
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
                response={"application/json"},
                description="Successfully retrieved searched jobs",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved searched jobs",
                            "data": [
                                {
                                    "id": "<uuid>",
                                    "title": "<string>",
                                    "recruiter": "<string>",
                                    "job_image": "<string:image_url>",
                                    "location": "<string>",
                                    "type": "<string>",
                                    "salary": "<decimal or float>",
                                    "is_saved": "<bool>",
                                }
                            ]
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="No jobs found",
                examples=[
                    OpenApiExample(
                        name="Not found",
                        value={
                            "status": "failure",
                            "message": "No jobs found",
                            "code": "non_existent"
                        }
                    )
                ]
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        search = self.request.query_params.get('search')

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
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No jobs found",
                               status_code=status.HTTP_404_NOT_FOUND)


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
                response={"application/json"},
                description="Retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "profile_name": "<string>",
                            "tip": {
                                "id": "<uuid>",
                                "title": "<string>",
                                "author_image": "<string:image_url>",
                            },
                            "job_types": [
                                {
                                    "id": "<uuid>",
                                    "name": "<string>"
                                },
                            ],
                            "jobs": [
                                {
                                    "id": "<uuid>",
                                    "title": "<string>",
                                    "recruiter": "<string>",
                                    "job_image": "<string:image_url>",
                                    "location": "<string>",
                                    "type": "<string>",
                                    "salary": "<decimal or float>",
                                    "is_saved": "<bool>",
                                },
                            ]
                        }
                    )
                ]
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
                This endpoint allows an authenticated job seeker to retrieve a single job using the id passed in the path parameter.
                """
        ),
        tags=["Job (Seeker)"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Successfully retrieved job details",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "id": "<uuid>",
                            "title": "<string>",
                            "recruiter": "<string>",
                            "job_image": "<string:image_url>",
                            "location": "<string>",
                            "type": "<string>",
                            "salary": "<decimal or float>",
                            "is_saved": "<bool>",
                            "requirements": [
                                {
                                    "id": "<uuid>",
                                    "requirement": "<string>"
                                },
                            ],
                            "url": "<string>"
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="Job with this id does not exist",
                examples=[
                    OpenApiExample(
                        name="Error Response",
                        value={
                            "status": "failure",
                            "message": "Job with this id does not exist",
                            "code": "non_existent",
                        }
                    )
                ]
            )
        }
    )
    def get(self, request, *args, **kwargs):
        job_id = self.kwargs.get('id')

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
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Job with this id does not exist",
                               status_code=status.HTTP_404_NOT_FOUND)


class JobApplyView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)
    serializer_class = JobApplySerializer

    @extend_schema(
        summary="Apply for a job",
        description=(
                """
                This endpoint allows a authenticated user to apply for a job by passing the id of the job in the path parameter,
                and also pass in the required fields in the request body. ``CV: File``: Only accepts ``.pdf``, ``.doc`` and ``.docx`` files
                """
        ),
        request=JobApplySerializer,
        tags=["Job (Seeker)"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response="Successfully applied for job"
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="Job with this id does not exist",
                examples=[
                    OpenApiExample(
                        name="Error Response",
                        value={
                            "status": "failure",
                            "message": "Job with this id does not exist",
                            "code": "non_existent",
                        }
                    )
                ]
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                response={"application/json"},
                description="Already applied for this job",
                examples=[
                    OpenApiExample(
                        name="Conflict Error Response",
                        value={
                            "status": "failure",
                            "message": "Already applied for this job",
                            "code": "already_exists",
                        }
                    )
                ]
            )
        }
    )
    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        job_id = self.kwargs.get('id')
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        job = Job.objects.get(id=job_id)  # Try to get the job

        if job is None:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Job with this id does not exist", data={},
                               status_code=status.HTTP_404_NOT_FOUND)

        # Check if the user has already applied to the job and their application is still pending
        existing_pending_application = AppliedJob.objects.filter(job=job, user=request.user,
                                                                 status=STATUS_PENDING).exists()
        if existing_pending_application:
            raise RequestError(err_code=ErrorCode.ALREADY_EXISTS,
                               err_msg="You have already applied to this job and your application is still pending.",
                               data={}, status_code=status.HTTP_409_CONFLICT)

        # Check if the user has already applied to the job and their application has been accepted
        existing_accepted_application = AppliedJob.objects.filter(job=job, user=request.user,
                                                                  status=STATUS_ACCEPTED).exists()
        if existing_accepted_application:
            raise RequestError(err_code=ErrorCode.ALREADY_EXISTS,
                               err_msg="You have already applied to this job and your application has been accepted.",
                               data={}, status_code=status.HTTP_409_CONFLICT)

        AppliedJob.objects.create(job=job, cv=serializer.validated_data.get("cv"),
                                  user=request.user)  # create the applied job

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
        tags=['Job (Seeker)'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Successfully retrieved searched applied jobs",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved searched applied jobs",
                            "data": [
                                {
                                    "id": "<uuid>",
                                    "title": "Software Developer",
                                    "recruiter": "Google",
                                    "job_image": "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png",
                                    "location": "New York",
                                    "type": "Full-time",
                                    "status": "PENDING",
                                }
                            ]
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="No applied jobs found",
                examples=[
                    OpenApiExample(
                        name="Error Response",
                        value={
                            "status": "failure",
                            "message": "No applied jobs found",
                            "code": "non_existent",
                        }
                    )
                ]
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        search = self.request.query_params.get('search')

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
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No applied jobs found", data={}, )


class AppliedJobDetailsView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @extend_schema(
        summary="Get applied job details",
        description=(
                """
                This endpoint allows an authenticated job seeker to retrieve the details of the applied job, 
                you can pass in the `id` of the applied job to the path parameter.
                """
        ),
        tags=["Job  (Seeker)"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Successfully retrieved applied job details",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved applied job details",
                            "data": {
                                "id": "<uuid>",
                                "title": "Software Developer",
                                "recruiter": "Google",
                                "job_image": "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png",
                                "location": "New York",
                                "type": "Full Time",
                                "status": "PENDING",
                                "review": "<string>",

                            }
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="Applied job with this id does not exist",
                examples=[
                    OpenApiExample(
                        name="Error Response",
                        value={
                            "status": "failure",
                            "message": "Applied job with this id does not exist",
                            "code": "non_existent",
                        }
                    )
                ]
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        applied_job_id = self.kwargs.get('id')

        applied_job = AppliedJob.objects.get(id=applied_job_id)

        if applied_job is None:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Applied job with this id does not exist")

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
        return CustomResponse.success(message="Successfully retrieved applied job details", data=data)


class FilterAppliedJobsView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = AppliedJobFilter

    @extend_schema(
        summary="Get all applications and filter",
        description=(
                """
                This endpoint gets all applications the authenticated job seeker has applied to with some filters option
                """
        ),
        parameters=[
            OpenApiParameter('status', type=OpenApiTypes.STR, required=False, description="Filter jobs by type"),
        ],
        tags=["Job  (Seeker)"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Retrieved successfully",
                            "data": [
                                {
                                    "id": "<uuid>",
                                    "title": "Software Developer",
                                    "recruiter": "Google",
                                    "job_image": "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png",
                                    "status": "PENDING",
                                    "location": "New York",
                                    "type": "Full Time",
                                    "review": "<string>",
                                }
                            ]
                        }
                    )
                ]
            )
        }
    )
    def get(self, request):
        queryset = AppliedJob.objects.all().order_by('-created')
        queryset = self.filterset_class(data=request.GET, queryset=queryset).qs
        data = [
            {
                "id": application.id,
                "title": application.job.title,
                "recruiter": application.job.recruiter.company_profile.name,
                "job_image": application.job.image_url,
                "status": application.status,
                "salary": application.salary,
                "location": application.job.location,
                "type": application.type.name,
                "review": application.review
            }
            for application in queryset
        ]
        return CustomResponse.success(message="Retrieved successfully", data=data)


class CreateDeleteSavedJobsView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @extend_schema(
        summary="Create saved job",
        description=(
                """
                This endpoint allows a job seeker to create a saved job, pass in the `id` of the job to the path parameter.
                """
        ),
        tags=["Job (Seeker)"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Successfully saved job",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully saved job",
                            "data": {
                                "id": "<uuid>",
                                "job_id": "<uuid>",
                                "title": "Software Developer",
                                "recruiter": "Google",
                                "job_image": "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png",
                                "location": "New York",
                                "type": "Full Time",
                                "salary": "<decimal or float>",
                                "is_saved": "<bool>"
                            }
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="Job with this id does not exist",
                examples=[
                    OpenApiExample(
                        name="Error Response",
                        value={
                            "status": "failure",
                            "message": "Job with this id does not exist",
                            "code": "non_existent",
                        }
                    )
                ]
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                response={"application/json"},
                description="Job is already saved",
                examples=[
                    OpenApiExample(
                        name="Error Response",
                        value={
                            "status": "failure",
                            "message": "Job is already saved",
                            "code": "already_exists",
                        }
                    )
                ]
            )
        }
    )
    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        job_id = self.kwargs.get('id')
        job = Job.objects.get(id=job_id)

        if job is None:
            raise RequestError(ErrorCode.NON_EXISTENT, err_msg="Job with this id does not exist", data={},
                               status_code=status.HTTP_404_NOT_FOUND)

        if job.is_saved_by_user(request.user):
            raise RequestError(ErrorCode.ALREADY_EXISTS, err_msg="Job is already saved", data={},
                               status_code=status.HTTP_409_CONFLICT)

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
        return CustomResponse.success(message="Successfully saved job", data=data)

    @extend_schema(
        summary="Delete saved job",
        description=(
                """
                This endpoint allows a job seeker to delete a saved job, pass in the `id` of the saved job to the path parameter.
                """
        ),
        tags=["Job (Seeker)"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"status": "success", "message": "Successfully deleted saved job"},
                description="Successfully deleted saved job",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully deleted saved job",
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"status": "failure", "message": "Saved job with this id does not exist"},
                description="Saved job with this id does not exist",
                examples=[
                    OpenApiExample(
                        name="Error Response",
                        value={
                            "status": "failure",
                            "message": "Saved job with this id does not exist",
                        }
                    )
                ]
            ),
        }
    )
    def delete(self, request, *args, **kwargs):
        saved_job_id = self.kwargs.get('id')

        saved_job = SavedJob.objects.get(id=saved_job_id, user=request.user)

        if saved_job is None:
            raise RequestError(ErrorCode.NON_EXISTENT, err_msg="Saved job with this id does not exist", data={},
                               status_code=status.HTTP_404_NOT_FOUND)

        saved_job.delete()
        return CustomResponse.success(message="Successfully deleted saved job")


class RetrieveAllSavedJobsView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @extend_schema(
        summary="Get saved jobs",
        description=(
                """
                Retrieve all saved jobs: This endpoint allows a job seeker to get a list of saved jobs.
                `P.S`: Use the job id to get the details of the job using the job details endpoint.
                """
        ),
        tags=["Job (Seeker)"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Successfully retrieved saved job",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved saved job",
                            "data": {
                                "id": "<uuid>",
                                "job_id": "<uuid>",
                                "title": "Software Developer",
                                "recruiter": "Google",
                                "job_image": "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png",
                                "location": "New York",
                                "type": "Full Time",
                                "salary": "<decimal or float>",
                                "is_saved": "<bool>"
                            }
                        }
                    )
                ]
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
                response={"application/json"},
                description="Successfully retrieved posted vacancies",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved posted vacancies",
                            "data": [
                                {
                                    "id": "<uuid>",
                                    "title": "Software Developer",
                                    "recruiter": "Google",
                                    "job_image": "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png",
                                    "location": "New York",
                                    "type": "Full Time",
                                    "salary": "<decimal or float>",
                                    "active": "<bool>",
                                },
                            ]
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"status": "failure", "message": "No vacancies found"},
                description="No vacancies found",
                examples=[
                    OpenApiExample(
                        name="Error Response",
                        value={
                            "status": "failure",
                            "message": "No vacancies found",
                        }
                    )
                ]
            ),
        }
    )
    def get(self, request, *args, **kwargs):
        search = self.request.query_params.get('search')

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
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No vacancies found",
                               status_code=status.HTTP_404_NOT_FOUND)


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


class RetrieveAllJobTypesView(APIView):
    permission_classes = (IsAuthenticatedCompany,)

    @extend_schema(
        summary="Retrieve all job types",
        description=(
                "This endpoint allows an authenticated job recruiter to retrieve all job types"
        ),
        tags=['Job Recruiter Home'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully retrieved all job types",
            ),
        }
    )
    def get(self, request):
        job_types = JobType.objects.all()
        data = [
            {
                "id": job_type.id,
                "name": job_type.name
            }
            for job_type in job_types
        ]
        return CustomResponse.success(message="Successfully retrieved all job types", data=data)


class CreateVacanciesView(APIView):
    permission_classes = (IsAuthenticatedCompany,)
    serializer_class = CreateJobSerializer

    @extend_schema(
        summary="Create a new job",
        description=(
                "This endpoint allows an authenticated job recruiter to create a new job"
        ),
        tags=['Job (Recruiter)'],
        request=CreateJobSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                description="Successfully created a new job",
            ),
        }
    )
    @transaction.atomic()
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        requirements_data = serializer.validated_data.pop('requirements', [])
        created_job = Job.objects.create(recruiter=request.user, **serializer.validated_data)

        # create JobRequirements objects for each requirement
        job_requirements = [
            JobRequirement(job=created_job, requirement=requirement)
            for requirement in requirements_data
        ]
        JobRequirement.objects.bulk_create(job_requirements)

        data = {
            "id": created_job,
            "title": created_job.title,
            "job_image": created_job.image_url,
            "recruiter": created_job.recruiter.company_profile.name,
        }

        return CustomResponse.success(message="Successfully created a new job", data=data,
                                      status_code=status.HTTP_201_CREATED)


class UpdateDeleteVacancyView(APIView):
    permission_classes = (IsAuthenticatedCompany,)
    serializer_class = UpdateVacanciesSerializer

    @extend_schema(
        summary="Update a job vacancy",
        description=(
                "This endpoint allows an authenticated job recruiter to update a job"
        ),
        tags=['Job (Recruiter)'],
        request=UpdateVacanciesSerializer,
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                description="Successfully updated a job",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Job not found",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Missing required parameters",
            )
        }
    )
    def update(self, request, *args, **kwargs):
        vacancy_id = self.kwargs.get('id')
        if vacancy_id is None:
            return CustomResponse.error(message="Missing required parameters", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            job_instance = Job.objects.get(id=vacancy_id, recruiter=request.user)
        except Job.DoesNotExist:
            return CustomResponse.error(message="Job not found", status_code=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        requirements_data = serializer.validated_data.pop('requirements', [])

        for key, value in serializer.validated_data.items():
            setattr(job_instance, key, value)
        job_instance.save()

        requirements_to_create = []

        for requirement in requirements_data:
            # Try to get the existing requirement
            existing_requirement, created = JobRequirement.objects.get_or_create(job=job_instance,
                                                                                 requirement=requirement)
            # If the requirement didn't exist, we need to update it
            if not created:
                existing_requirement.requirement = requirement.requirement
                requirements_to_create.append(existing_requirement)

        # Use bulk_create() to update the existing requirements
        JobRequirement.objects.bulk_create(requirements_to_create)

        data = {
            "id": job_instance.id,
            "title": job_instance.title,
            "job_image": job_instance.image_url,
            "recruiter": job_instance.recruiter.company_profile.name,
        }

        return CustomResponse.success(message="Successfully updated a job", data=data)

    @extend_schema(
        summary="Delete a job",
        description=(
                "This endpoint allows an authenticated job recruiter to delete a job"
        ),
        tags=['Job (Recruiter)'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Successfully deleted a job",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Job not found",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Missing required parameters",
            )
        }
    )
    def delete(self, request, *args, **kwargs):
        vacancy_id = self.kwargs.get('id')
        if vacancy_id is None:
            return CustomResponse.error(message="Missing required parameters", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            job_instance = Job.objects.get(id=vacancy_id, recruiter=request.user)
        except Job.DoesNotExist:
            return CustomResponse.error(message="Job not found", status_code=status.HTTP_404_NOT_FOUND)

        job_instance.delete()

        return CustomResponse.success(message="Successfully deleted a job")


class UpdateAppliedJobView(APIView):
    permission_classes = (IsAuthenticatedCompany,)
    serializer_class = UpdateAppliedJobSerializer

    @extend_schema(
        summary="Update applied job",
        description=(
                "This endpoint allows an authenticated job seeker to update an applied job"
        ),
        tags=['Job (Recruiter)'],
        request=UpdateAppliedJobSerializer,
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                description="Successfully updated an applied job",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="No application with this ID",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Missing required parameters",
            )
        }
    )
    def patch(self, request, *args, **kwargs):
        applied_job_id = self.kwargs.get('id')
        if applied_job_id is None:
            return CustomResponse.error(message="Missing required parameters", status_code=status.HTTP_400_BAD_REQUEST)

        try:
            applied_job = AppliedJob.objects.get(id=applied_job_id, job__recruiter=request.user)
        except AppliedJob.DoesNotExist:
            return CustomResponse.error(message="No application with this ID", status_code=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        for key, value in serializer.validated_data.items():
            setattr(applied_job, key, value)
        applied_job.save()

        if applied_job.status == STATUS_ACCEPTED:
            Notification.objects.create(
                user=applied_job.user,
                notification_type=NOTIFICATION_APPLICATION_ACCEPTED,
                message=f"Your application for {applied_job.job.title} has been accepted!",
            )
        elif applied_job.status == STATUS_REJECTED:
            Notification.objects.create(
                user=applied_job.user,
                notification_type=NOTIFICATION_APPLICATION_REJECTED,
                message=f"Your application for {applied_job.job.title} has been rejected!",
            )
        elif applied_job.status == STATUS_SCHEDULED_FOR_INTERVIEW:
            Notification.objects.create(
                user=applied_job.user,
                notification_type=NOTIFICATION_APPLICATION_SCHEDULED_FOR_INTERVIEW,
                message=f"Your application for {applied_job.job.title} has been scheduled for an interview!",
            )

        data = {
            "id": applied_job.id,
            "job": applied_job.job.title,
            "applicant": applied_job.user.employee_profile.full_name,
            "applicant_image": applied_job.user.employee_profile.image_url,
            "cv": applied_job.cv.url,
            "status": applied_job.status,
            "review": applied_job.review,
            "interview_date": applied_job.interview_date
        }

        return CustomResponse.success(message="Successfully updated an applied job", data=data)
