from django.urls import path

from apps.jobs.views import *

urlpatterns = [
    path('', JobsHomeView.as_view(), name="jobs_home"),
    path('search', SearchJobsView.as_view(), name="search_jobs"),
]
