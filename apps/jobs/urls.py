from django.urls import path

from apps.jobs.views import *

urlpatterns = [
    path('', JobsHomeView.as_view(), name="jobs-home"),
    path('search', SearchJobsView.as_view(), name="search-jobs"),
    path('job/<str:id>', JobDetailsView.as_view(), name="job-details"),
    path('job/apply/<str:id>', JobApplyView.as_view(), name="job-apply"),
]
