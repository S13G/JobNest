from drf_spectacular.utils import OpenApiResponse, extend_schema, OpenApiExample
from rest_framework import status
from rest_framework.generics import GenericAPIView

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.responses import CustomResponse
from apps.social_auth.serializers import JobSeekerGoogleSocialAuthSerializer, JobRecruiterGoogleSocialAuthSerializer


class JobSeekerGoogleSocialAuthView(GenericAPIView):
    serializer_class = JobSeekerGoogleSocialAuthSerializer

    @extend_schema(
        summary="Google Authentication Endpoint for registering and logging in Job Seeker profile",
        description=(
                """
                This endpoint allows users to authenticate through Google and automatically creates a job seeker profile for them if it doesn't exist.
                """
        ),
        request=JobSeekerGoogleSocialAuthSerializer,
        tags=['Social Authentication'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Success",
                examples=[
                    OpenApiExample(
                        name="Success",
                        value={
                            "status": "success",
                            "message": "Successfully authenticated",
                            "data": {
                                "tokens": {
                                    "access": "<access-token>",
                                    "refresh": "<refresh-token>"
                                },
                                "data": {
                                    "user_id": "0ba94e40-b20e-4eaa-b864-2813933de027",
                                    "profile": {
                                        "user_id": "0ba94e40-b20e-4eaa-b864-2813933de027",
                                        "id": "b047222e-b0e5-46e4-bec1-5640b2c9eb81",
                                        "name": "",
                                        "country": "",
                                        "email": "<email-address>",
                                        "avatar": "",
                                        "address": ""
                                    }
                                }
                            }
                        }
                    )
                ]
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                response={"application/json": {}},
                description="Conflict",
                examples=[
                    OpenApiExample(
                        name="Conflict",
                        value={
                            "status": "failure",
                            "message": "User already has a company_profile.",
                            "code": "already_exists"
                        }
                    )
                ]
            )
        }
    )
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


class JobRecruiterGoogleSocialAuthView(GenericAPIView):
    serializer_class = JobRecruiterGoogleSocialAuthSerializer

    @extend_schema(
        summary="Google Authentication Endpoint for registering and logging in Job recruiter profile",
        description=(
                """
                This endpoint allows users to authenticate through Google and automatically creates a job seeker profile for them if it doesn't exist.
                """
        ),
        request=JobRecruiterGoogleSocialAuthSerializer,
        tags=['Social Authentication'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Success",
                examples=[
                    OpenApiExample(
                        name="Success",
                        value={
                            "status": "success",
                            "message": "Successfully authenticated",
                            "data": {
                                "tokens": {
                                    "access": "<access-token>",
                                    "refresh": "<refresh-token>"
                                },
                                "data": {
                                    "user_id": "0ba94e40-b20e-4eaa-b864-2813933de027",
                                    "profile": {
                                        "user_id": "0ba94e40-b20e-4eaa-b864-2813933de027",
                                        "id": "b047222e-b0e5-46e4-bec1-5640b2c9eb81",
                                        "name": "",
                                        "country": "",
                                        "email": "<email-address>",
                                        "avatar": "",
                                        "address": ""
                                    }
                                }
                            }
                        }
                    )
                ]
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                response={"application/json"},
                description="Conflict",
                examples=[
                    OpenApiExample(
                        name="Conflict",
                        value={
                            "status": "failure",
                            "message": "User already has a company_profile.",
                            "code": "already_exists"
                        }
                    )
                ]
            )
        }
    )
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
