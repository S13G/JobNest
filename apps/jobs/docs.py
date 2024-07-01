import pycountry
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status

from apps.jobs.models import JobType


def country_docs():
    return extend_schema(
        summary="Get all countries",
        description=
        """
        This endpoint retrieve all countries
        """,
        tags=['Countries'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Successfully retrieved all countries",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved all countries",
                            "data": [
                                {
                                    "name": "Afghanistan",
                                    "alpha_2": "AF"
                                }
                            ]
                        }
                    )
                ]
            )
        }
    )


def search_jobs_docs():
    return extend_schema(
        summary="Search jobs",
        parameters=[
            OpenApiParameter(name="search", type=OpenApiTypes.STR, required=False)
        ],
        description=
        """
        This endpoint allows an authenticated job seeker to search for jobs
        """,
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
                                    "id": "ee33b210-93c0-46c6-abea-58841db8dec9",
                                    "title": "Backend Engineer",
                                    "recruiter": {
                                        "id": "9bed0097-7c05-4849-8cfb-b4d28ccaf9c0",
                                        "name": "Amazon",
                                    },
                                    "job_image": "/media/static/jobs/Screenshot_from_2024-07-01_10-55-13.png",
                                    "location": "Burundi",
                                    "type": "Software",
                                    "salary": 500000,
                                    "is_saved": False
                                },
                                {
                                    "id": "9bed0097-7c05-4849-8cfb-b4d28ccaf9c0",
                                    "title": "Software Developer",
                                    "recruiter": {
                                        "id": "9bed0097-7c05-4849-8cfb-b4d28ccaf9c0",
                                        "name": "Apple",
                                    },
                                    "job_image": "/media/static/jobs/Screenshot_from_2024-07-01_06-53-03.png",
                                    "location": "Åland Islands",
                                    "type": "Software",
                                    "salary": 20000,
                                    "is_saved": False
                                }
                            ]
                        }
                    )
                ]
            )
        }
    )


def job_home_docs():
    return extend_schema(
        summary="Job seeker home page",
        description=(
            """
            Get home page: Search, Retrieve all job types, and all jobs and also tip including notifications.
            """
        ),
        parameters=[
            OpenApiParameter('type', type=OpenApiTypes.STR, required=False, description="Filter jobs by type",
                             enum=JobType.objects.values_list('name', flat=True)),

            OpenApiParameter('location', type=OpenApiTypes.STR, required=False,
                             description="Filter jobs by location: Pass in the countries alpha 2 to get the result",
                             enum=[country.alpha_2 for country in pycountry.countries]),

            OpenApiParameter('salary_min', type=OpenApiTypes.FLOAT, required=False,
                             description="Filter jobs by salary"),

            OpenApiParameter('salary_max', type=OpenApiTypes.FLOAT, required=False,
                             description="Filter jobs by salary"),
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
                            "status": "success",
                            "message": "Retrieved successfully",
                            "data": {
                                "profile_name": "",
                                "tip": {
                                    "id": "07ad4a3e-dee3-4c92-9eb0-490886a879fd",
                                    "title": "How to secure a job",
                                    "author_image": "/media/static/tip_author/Screenshot_from_2024-07-01_06-53-03.png"
                                },
                                "job_types": [
                                    {
                                        "id": "970cc79e-c3bb-47e5-817e-4657d33b0ac2",
                                        "name": "Product"
                                    },
                                    {
                                        "id": "3b10dad9-8f31-4131-930e-651c9292acfa",
                                        "name": "AI"
                                    },
                                    {
                                        "id": "7ea01e78-e924-43c8-9cc1-1dfad9bc31b3",
                                        "name": "Software"
                                    },
                                    {
                                        "id": "619d11e0-5c3b-4167-b714-459509a28a7f",
                                        "name": "Engineering"
                                    }
                                ],
                                "jobs": [
                                    {
                                        "id": "ee33b210-93c0-46c6-abea-58841db8dec9",
                                        "title": "Backend Engineer",
                                        "recruiter": {
                                            "id": "9bed0097-7c05-4849-8cfb-b4d28ccaf9c0",
                                            "name": "Amazon",
                                        },
                                        "job_image": "/media/static/jobs/Screenshot_from_2024-07-01_10-55-13.png",
                                        "location": "Burundi",
                                        "type": "Software",
                                        "salary": 500000,
                                        "is_saved": False
                                    },
                                    {
                                        "id": "9bed0097-7c05-4849-8cfb-b4d28ccaf9c0",
                                        "title": "Software Developer",
                                        "recruiter": {
                                            "id": "9bed0097-7c05-4849-8cfb-b4d28ccaf9c0",
                                            "name": "Apple",
                                        },
                                        "job_image": "/media/static/jobs/Screenshot_from_2024-07-01_06-53-03.png",
                                        "location": "Åland Islands",
                                        "type": "Software",
                                        "salary": 20000,
                                        "is_saved": False
                                    }
                                ]
                            }
                        }
                    )
                ]
            )
        }
    )


def job_details_docs():
    return extend_schema(
        summary="Retrieve single job",
        description=(
            """
            This endpoint allows an authenticated job seeker or recruiter to retrieve a single job using the id passed in the path parameter.
            """
        ),
        tags=["Job"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Successfully retrieved job details",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved job details",
                            "data": {
                                "id": "9bed0097-7c05-4849-8cfb-b4d28ccaf9c0",
                                "title": "Software Developer",
                                "recruiter": {
                                    "id": "9bed0097-7c05-4849-8cfb-b4d28ccaf9c0",
                                    "name": "Apple",
                                },
                                "job_image": "/media/static/jobs/Screenshot_from_2024-07-01_06-53-03.png",
                                "location": "Åland Islands",
                                "type": "Software",
                                "salary": 20000,
                                "is_saved": False,
                                "requirements": [
                                    {
                                        "id": "41b013f2-8465-4a70-b08d-9c6e3fb9329d",
                                        "requirement": "Good communication skills"
                                    },
                                    {
                                        "id": "96a50d10-b0f6-462d-b7e9-0b18f9b6907d",
                                        "requirement": "Javascript"
                                    },
                                    {
                                        "id": "1097126f-6089-46db-afc1-c2860befa62b",
                                        "requirement": "CSS"
                                    },
                                    {
                                        "id": "c1975c2c-d564-44b4-b42f-a323780f0746",
                                        "requirement": "HTML"
                                    }
                                ],
                                "url": "http://api.com/api/v1/jobs/job/9bed0097-7c05-4849-8cfb-b4d28ccaf9c0"
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
            )
        }
    )


def job_apply_docs():
    return extend_schema(
        summary="Apply for a job",
        description=(
            """
            This endpoint allows a authenticated job seeker to apply for a job by passing the id of the job in the path parameter,
            and also pass in the required fields in the request body. ``CV: File``: Only accepts ``.pdf``, ``.doc`` and ``.docx`` files
            """
        ),
        tags=["Job (Seeker)"],
        request=OpenApiTypes.BINARY,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Successfully applied for job",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully applied for job",
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
                description="Already applied for this job",
                examples=[
                    OpenApiExample(
                        name="Pending Applied Error Response",
                        value={
                            "status": "failure",
                            "message": "You have already applied to this job and your application is still pending.",
                            "code": "already_exists",
                        }
                    ),
                    OpenApiExample(
                        name="Accepted Error Response",
                        value={
                            "status": "failure",
                            "message": "You have already applied to this job and your application has been accepted.",
                            "code": "already_exists",
                        }
                    )
                ]
            )
        }
    )
