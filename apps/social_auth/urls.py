from django.urls import path

from apps.social_auth.views import *

urlpatterns = [
    path('job-seeker/google-auth', JobSeekerGoogleSocialAuthView.as_view(), name="job-seeker-google-auth"),
    path('job-recruiter/google-auth', JobRecruiterGoogleSocialAuthView.as_view(), name="job-recruiter-google-auth")
]
