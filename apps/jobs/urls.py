from django.urls import path

from apps.jobs.views import *

urlpatterns = [
    path('countries', ListCountriesView.as_view(), name="list-countries"),
    path('', JobsHomeView.as_view(), name="jobs-home"),
    path('search-jobs', SearchJobsView.as_view(), name="search-jobs"),
    path('job/<str:id>', JobDetailsView.as_view(), name="job-details"),
    path('job/apply/<str:id>', JobApplyView.as_view(), name="job-apply"),
    path('applied-jobs/search', AppliedJobsSearchView.as_view(), name="applied-jobs-search"),
    path('applied-job/<str:id>', AppliedJobDetailsView.as_view(), name="applied-job-details"),
    path('applied-jobs/filter', FilterAppliedJobsView.as_view(), name="filter-applied-jobs"),
    path('saved-jobs', RetrieveAllSavedJobsView.as_view(), name="saved-jobs"),
    path('saved-job/<str:id>', CreateDeleteSavedJobsView.as_view(), name="create-delete-saved-job"),
    path('vacancies/search', SearchVacanciesView.as_view(), name="search-vacancies"),
    path('vacancies/filter', VacanciesHomeView.as_view(), name="filter-vacancies"),
    path('job-types/all', RetrieveAllJobTypesView.as_view(), name='job-types-all'),
    path('create-job', CreateVacanciesView.as_view(), name="create-job"),
    path('job/update/delete/<str:id>', UpdateDeleteVacancyView.as_view(), name="update-delete-job"),
    path('applied-job/update/<str:id>', UpdateAppliedJobView.as_view(), name="update-applied-job"),
]
