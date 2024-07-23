from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status

from apps.social_auth.serializers import JobSeekerGoogleSocialAuthSerializer, JobRecruiterGoogleSocialAuthSerializer


def job_seeker_google_social_auth_doc():
    return extend_schema(
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


def job_recruiter_google_social_auth_doc():
    return extend_schema(
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
