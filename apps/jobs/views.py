from django.core.cache import cache
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAuthenticatedEmployee, IsAuthenticatedCompany
from apps.common.responses import CustomResponse
from apps.jobs.docs.docs import *
from apps.jobs.filters import JobFilter, AppliedJobFilter, VacanciesFilter
from apps.jobs.selectors import *
from apps.jobs.serializers import CreateJobSerializer, UpdateVacanciesSerializer, UpdateAppliedJobSerializer, \
    JobApplySerializer
from apps.misc.models import Tip


# # Create your views here.

class ListCountriesView(APIView):

    @country_docs()
    @method_decorator(cache_page(60 * 60 * 24 * 7, key_prefix="retrieve_countries"))
    def get(self, request):
        countries = [
            {
                'name': country.name,
                'alpha_2': country.alpha_2,
            }
            for country in pycountry.countries
        ]

        return CustomResponse.success(message="Retrieved successfully", data=countries)


class SearchJobsView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @search_jobs_docs()
    def get(self, request, *args, **kwargs):
        search = request.query_params.get('search', '')
        current_user = request.user

        data = get_searched_jobs(query=search, user=current_user)
        return CustomResponse.success(message="Successfully retrieved searched jobs", data=data)


class JobsHomeView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = JobFilter

    @job_home_docs()
    def get(self, request):
        # Get query param
        query_params = request.GET.urlencode()

        # Set key for query_param search results
        cache_key = f"retrieve_jobs_{query_params}"
        cached_data = cache.get(cache_key)

        # Return cached data if it exists
        if cached_data:
            return CustomResponse.success(message="Retrieved successfully", data=cached_data)

        current_user = request.user
        profile_name = current_user.employee_profile.full_name

        tip = Tip.objects.only('title').order_by('-created').first()

        job_types = JobType.objects.only('name')

        queryset = Job.objects.get_active_jobs()
        queryset = self.filterset_class(data=request.GET, queryset=queryset).qs

        data = job_home_data(queryset=queryset, profile_name=profile_name, tip=tip, job_types=job_types,
                             user=current_user)

        # Set cache data
        cache.set(cache_key, data, 60 * 60)
        return CustomResponse.success(message="Retrieved successfully", data=data)


class JobDetailsView(APIView):
    permission_classes = (IsAuthenticated,)

    @job_details_docs()
    @method_decorator(cache_page(60 * 60, key_prefix="retrieve_job"))
    def get(self, request, *args, **kwargs):
        job_id = kwargs.get('id')

        job = get_job_by_id(job_id=job_id)

        data = job_details_data(job=job, user=request.user, request=request)
        return CustomResponse.success(message="Successfully retrieved job details", data=data)


class JobApplyView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)
    serializer_class = JobApplySerializer

    @job_apply_docs()
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        job_id = kwargs.get('id')

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        job = get_job_by_id(job_id=job_id)

        apply_to_job(job=job, user=request.user, data=data)

        return CustomResponse.success(message="Successfully applied for job")


class AppliedJobsSearchView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @applied_jobs_search_docs()
    def get(self, request, *args, **kwargs):
        search = request.query_params.get('search', '')

        data = get_applied_jobs(search=search)
        return CustomResponse.success(message="Successfully retrieved searched applied jobs", data=data)


class AppliedJobDetailsView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @applied_job_details_docs()
    @method_decorator(cache_page(60 * 60, key_prefix="retrieve_applied_job"))
    def get(self, request, *args, **kwargs):
        applied_job_id = kwargs.get('id')

        data = applied_job_details_data(job_id=applied_job_id, current_user=request.user)
        return CustomResponse.success(message="Successfully retrieved applied job details", data=data)


class FilterAppliedJobsView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = AppliedJobFilter

    @filter_applied_jobs_docs()
    def get(self, request):
        current_user = request.user

        # Serialize query parameters to use in the cache key
        query_params = request.GET.urlencode()
        cache_key = f"filter_applied_jobs_{current_user.id}_{query_params}"

        # Check if cached data exists
        cached_data = cache.get(cache_key)
        if cached_data:
            return CustomResponse.success(message="Retrieved successfully", data=cached_data)

        queryset = AppliedJob.objects.filter(user=current_user).order_by('-created')
        filtered_queryset = self.filterset_class(data=request.GET, queryset=queryset).qs

        data = filter_applied_jobs_data(queryset=filtered_queryset)

        # Set cache data
        cache.set(cache_key, data, 60 * 60 * 24)
        return CustomResponse.success(message="Retrieved successfully", data=data)


class CreateDeleteSavedJobsView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @create_saved_jobs_docs()
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        job_id = kwargs.get('id')
        job = get_job_by_id(job_id=job_id)

        if job.is_saved_by_user(request.user):
            raise RequestError(ErrorCode.ALREADY_EXISTS, err_msg="Job is already saved",
                               status_code=status.HTTP_409_CONFLICT)

        data = create_saved_jobs(job=job, current_user=request.user)
        return CustomResponse.success(message="Successfully saved job", data=data)

    @delete_saved_jobs_docs()
    def delete(self, request, *args, **kwargs):
        saved_job_id = kwargs.get('id')

        delete_saved_jobs(job_id=saved_job_id, current_user=request.user)
        return CustomResponse.success(message="Successfully deleted saved job", status_code=status.HTTP_204_NO_CONTENT)


class RetrieveAllSavedJobsView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @retrieve_all_saved_jobs_docs()
    def get(self, request):
        current_user = request.user

        # Set key for query_param search results
        cache_key = f"retrieve_saved_jobs_{current_user.id}"

        # Check if cached data exists
        cached_data = cache.get(cache_key)
        if cached_data:
            return CustomResponse.success(message="Successfully retrieved saved jobs", data=cached_data)

        saved_jobs = SavedJob.objects.select_related('job', 'user').filter(user=request.user)

        data = get_saved_jobs_data(saved_jobs=saved_jobs, current_user=request.user)

        # Set cache data
        cache.set(cache_key, data, 60 * 60 * 24)

        return CustomResponse.success(message="Successfully retrieved saved jobs", data=data)


"""
COMPANY SECTION
"""


class SearchVacanciesView(APIView):
    permission_classes = (IsAuthenticatedCompany,)

    @search_vacancies_docs()
    def get(self, request, *args, **kwargs):
        search = request.query_params.get('search', '')

        data = get_search_vacancies(search=search)
        return CustomResponse.success(message="Successfully retrieved searched vacancies", data=data)


class VacanciesHomeView(APIView):
    permission_classes = (IsAuthenticatedCompany,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = VacanciesFilter

    @vacancies_home_docs()
    def get(self, request):
        # Get query param
        query_params = request.GET.urlencode()

        # Set key for query_param search results
        cache_key = f"retrieve_vacancies_{query_params}"

        # Return cached data if it exists
        cached_data = cache.get(cache_key)
        if cached_data:
            return CustomResponse.success(message="Retrieved successfully", data=cached_data)

        profile_name = request.user.company_profile.name

        my_vacancies = Job.objects.filter(recruiter=request.user).order_by('-created')
        all_applied_jobs = AppliedJob.objects.filter(job__recruiter=request.user).order_by('-created')

        queryset = self.filterset_class(data=request.GET, queryset=my_vacancies).qs

        data = vacancies_home_data(queryset=queryset, profile_name=profile_name, applied_jobs=all_applied_jobs)

        # Set cache data
        cache.set(cache_key, data, 60 * 60)
        return CustomResponse.success(message="Retrieved successfully", data=data)


class RetrieveAllJobTypesView(APIView):
    permission_classes = (IsAuthenticatedCompany,)

    @retrieve_all_job_types_docs()
    @method_decorator(cache_page(60 * 60 * 24 * 7, key_prefix="retrieve_job_types"))
    def get(self, request):
        job_types = JobType.objects.only('id', 'name')

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

    @create_vacancies_docs()
    @transaction.atomic
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serialized_data = serializer.validated_data

        requirements_data = serialized_data.pop('requirements', [])

        data = create_vacancy_application(current_user=request.user, data=serialized_data,
                                          requirements_data=requirements_data)

        return CustomResponse.success(message="Successfully created a new job", data=data,
                                      status_code=status.HTTP_201_CREATED)


class UpdateDeleteVacancyView(APIView):
    permission_classes = (IsAuthenticatedCompany,)
    serializer_class = UpdateVacanciesSerializer

    @update_vacancy_docs()
    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        vacancy_id = kwargs.get('id')
        job_instance = Job.objects.get_or_none(id=vacancy_id, recruiter=request.user)

        if job_instance is None:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Job not found",
                               status_code=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serialized_data = serializer.validated_data

        requirements_data = serialized_data.pop('requirements', [])

        data = update_vacancy_data(serialized_data=serialized_data, requirements_data=requirements_data,
                                   job_instance=job_instance)
        return CustomResponse.success(message="Successfully updated a job", data=data,
                                      status_code=status.HTTP_202_ACCEPTED)

    @delete_vacancy_docs()
    def delete(self, request, *args, **kwargs):
        vacancy_id = kwargs.get('id')

        job_instance = Job.objects.get_or_none(id=vacancy_id, recruiter=request.user)

        if job_instance is None:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="Job not found",
                               status_code=status.HTTP_404_NOT_FOUND)

        job_instance.delete()
        return CustomResponse.success(message="Successfully deleted a job", status_code=status.HTTP_204_NO_CONTENT)


class UpdateAppliedJobView(APIView):
    permission_classes = (IsAuthenticatedCompany,)
    serializer_class = UpdateAppliedJobSerializer

    @update_applied_job_docs()
    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        applied_job_id = kwargs.get('id')

        applied_job = AppliedJob.objects.get_or_none(id=applied_job_id, job__recruiter=request.user)
        if applied_job is None:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No application with this ID",
                               status_code=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serialized_data = serializer.validated_data

        data = update_applied_job_data(serialized_data=serialized_data, applied_job=applied_job)

        return CustomResponse.success(message="Successfully updated an applied job", data=data,
                                      status_code=status.HTTP_202_ACCEPTED)
