from django.db import transaction
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.responses import CustomResponse
from apps.social_auth.docs.docs import job_seeker_google_social_auth_doc, job_recruiter_google_social_auth_doc
from apps.social_auth.serializers import JobSeekerGoogleSocialAuthSerializer, JobRecruiterGoogleSocialAuthSerializer


class JobSeekerGoogleSocialAuthView(APIView):
    serializer_class = JobSeekerGoogleSocialAuthSerializer

    @job_seeker_google_social_auth_doc()
    @transaction.atomic
    def post(self, request):
        """
        Handles POST requests with "auth token" to get user information from Google.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        auth_token = serializer.validated_data['id_token']

        data = auth_token.get('data')

        if not data:
            raise RequestError(err_code=ErrorCode.SERVER_ERROR,
                               err_msg="Unable to retrieve user data. Please try again later.",
                               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        tokens = auth_token.get('tokens', {})

        return CustomResponse.success(message="Successfully authenticated", data={"tokens": tokens, "data": data},
                                      status_code=status.HTTP_200_OK)


class JobRecruiterGoogleSocialAuthView(APIView):
    serializer_class = JobRecruiterGoogleSocialAuthSerializer

    @job_recruiter_google_social_auth_doc()
    @transaction.atomic
    def post(self, request):
        """
        Handles POST requests with "auth token" to get user information from Google.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        auth_token = serializer.validated_data['id_token']

        data = auth_token.get('data')

        if not data:
            raise RequestError(err_code=ErrorCode.SERVER_ERROR,
                               err_msg="Unable to retrieve user data. Please try again later.",
                               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        tokens = auth_token.get('tokens', {})

        return CustomResponse.success(message="Successfully authenticated", data={"tokens": tokens, "data": data},
                                      status_code=status.HTTP_200_OK)
