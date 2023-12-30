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
from apps.jobs.filters import JobFilter
from apps.jobs.models import Job, JobType
from apps.misc.models import Tip


# # Create your views here.

class SearchJobsView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @extend_schema(
        summary="Search jobs",
        parameters=[OpenApiParameter(name="search", type=str, required=False)],
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
