import pycountry
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status

from apps.jobs.choices import STATUS_CHOICES
from apps.jobs.models import JobType


def country_docs():
    return extend_schema(
        summary="Get all countries",
        description="""
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
            OpenApiParameter(name="search", type=OpenApiTypes.STR)
        ],
        description="""
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
            OpenApiParameter('type', type=OpenApiTypes.STR, description="Filter jobs by type",
                             enum=JobType.objects.values_list('name', flat=True)),

            OpenApiParameter('location', type=OpenApiTypes.STR,
                             description="Filter jobs by location: Pass in the countries alpha 2 to get the result",
                             enum=[country.alpha_2 for country in pycountry.countries]),

            OpenApiParameter('salary_min', type=OpenApiTypes.FLOAT,
                             description="Filter jobs by salary"),

            OpenApiParameter('salary_max', type=OpenApiTypes.FLOAT,
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
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'cv': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        },
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


def applied_jobs_search_docs():
    return extend_schema(
        summary="Search applied jobs",
        parameters=[
            OpenApiParameter(name="search", type=OpenApiTypes.STR, required=False)
        ],
        description=(
            """
            This endpoint allows an authenticated job seeker to search for their applied jobs
            """
        ),
        tags=['Job (Seeker)'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Successfully retrieved searched applied jobs",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved searched applied jobs",
                            "data": [
                                {
                                    "id": "c57ad787-f80f-4e4f-9062-230637dee27a",
                                    "title": "Software Developer",
                                    "recruiter": {
                                        "id": "56a2d1f1-b25b-415b-85f1-ec1483f4c92c",
                                        "name": "Apple"
                                    },
                                    "job_image": "/media/static/jobs/Screenshot_from_2024-07-01_06-53-03.png",
                                    "status": "SCHEDULED FOR INTERVIEW"
                                },
                                {
                                    "id": "974dfd3c-00ab-4dde-8105-1f50bed62ffd",
                                    "title": "Backend Engineer",
                                    "recruiter": {
                                        "id": "4889ff71-9f07-4674-9b0b-13f29924f3c4",
                                        "name": "Amazon"
                                    },
                                    "job_image": "/media/static/jobs/Screenshot_from_2024-07-01_10-55-13.png",
                                    "status": "PENDING"
                                }
                            ]
                        }
                    )
                ]
            ),
        }
    )


def applied_job_details_docs():
    return extend_schema(
        summary="Get applied job details",
        description=(
            """
            This endpoint allows an authenticated job seeker to retrieve the details of the applied job, 
            you can pass in the `id` of the applied job to the path parameter.
            """
        ),
        tags=["Job  (Seeker)"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Successfully retrieved applied job details",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved applied job details",
                            "data": {
                                "id": "974dfd3c-00ab-4dde-8105-1f50bed62ffd",
                                "title": "Backend Engineer",
                                "recruiter": {
                                    "id": "eced692c-b5fe-4ebb-b4ca-7faacc0bbc7a",
                                    "name": "Amazon"
                                },
                                "job_image": "/media/static/jobs/Screenshot_from_2024-07-01_10-55-13.png",
                                "location": "Burundi",
                                "type": "Software",
                                "salary": 500000,
                                "status": "SCHEDULED FOR INTERVIEW",
                                "review": "I would like to have a meeting with you so we can discuss about your qualifications",
                                "interview_date": "2024-07-03T07:18:38.275000Z"
                            }
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="Applied job with this id does not exist",
                examples=[
                    OpenApiExample(
                        name="Error Response",
                        value={
                            "status": "failure",
                            "message": "Applied job with this id does not exist",
                            "code": "non_existent",
                        }
                    )
                ]
            ),
        }
    )


def filter_applied_jobs_docs():
    return extend_schema(
        summary="Get all applications and filter",
        description="""
        This endpoint gets all applications the authenticated job seeker has applied to with some filters option
        
        ```AVAILABLE FILTERS: PENDING, ACCEPTED, REJECTED, SCHEDULED FOR INTERVIEW```
        """,
        parameters=[
            OpenApiParameter('status', type=OpenApiTypes.STR, description="Filter jobs by type",
                             enum=[choice[0] for choice in STATUS_CHOICES]),
        ],
        tags=["Job  (Seeker)"],
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
                            "data": [
                                {
                                    "id": "c57ad787-f80f-4e4f-9062-230637dee27a",
                                    "title": "Software Developer",
                                    "recruiter": {
                                        "id": "eced692c-b5fe-4ebb-b4ca-7faacc0bbc7a",
                                        "name": "Amazon"
                                    },
                                    "job_image": "/media/static/jobs/Screenshot_from_2024-07-01_06-53-03.png",
                                    "status": "PENDING",
                                    "salary": 20000,
                                    "location": "Åland Islands",
                                    "type": "Software",
                                    "review": "",
                                    "interview_date": ""
                                }
                            ]
                        }
                    )
                ]
            )
        }
    )


def create_saved_jobs_docs():
    return extend_schema(
        summary="Create saved job",
        description=(
            """
            This endpoint allows a job seeker to save a job, pass in the `id` of the job to the path parameter.
            """
        ),
        tags=["Job (Seeker)"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Successfully saved job",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully saved job",
                            "data": {
                                "id": "3cd47f86-539f-4253-b2f3-974b45c7590a",
                                "job_id": "ee33b210-93c0-46c6-abea-58841db8dec9",
                                "title": "Backend Engineer",
                                "recruiter": {
                                    "id": "eced692c-b5fe-4ebb-b4ca-7faacc0bbc7a",
                                    "name": "Amazon"
                                },
                                "job_image": "/media/static/jobs/Screenshot_from_2024-07-01_10-55-13.png",
                                "location": "Burundi",
                                "type": "Software",
                                "salary": 500000,
                                "is_saved": True
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
            ),
            status.HTTP_409_CONFLICT: OpenApiResponse(
                response={"application/json"},
                description="Job is already saved",
                examples=[
                    OpenApiExample(
                        name="Error Response",
                        value={
                            "status": "failure",
                            "message": "Job is already saved",
                            "code": "already_exists",
                        }
                    )
                ]
            )
        }
    )


def delete_saved_jobs_docs():
    return extend_schema(
        summary="Delete saved job",
        description=(
            """
            This endpoint allows a job seeker to delete a saved job, pass in the `id` of the saved job to the path parameter.
            """
        ),
        tags=["Job (Seeker)"],
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                response={"application/json"},
                description="Successfully deleted saved job",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully deleted saved job",
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="Saved job with this id does not exist",
                examples=[
                    OpenApiExample(
                        name="Error Response",
                        value={
                            "status": "failure",
                            "message": "Saved job with this id does not exist",
                            "code": "non_existent",
                        }
                    )
                ]
            ),
        }
    )


def retrieve_all_saved_jobs_docs():
    return extend_schema(
        summary="Get saved jobs",
        description=(
            """
            Retrieve all saved jobs: This endpoint allows a job seeker to get a list of saved jobs.
            `P.S`: Use the job id to get the details of the job using the job details endpoint.
            """
        ),
        tags=["Job (Seeker)"],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Successfully retrieved saved job",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved saved jobs",
                            "data": {
                                "saved_jobs": [
                                    {
                                        "id": "3cd47f86-539f-4253-b2f3-974b45c7590a",
                                        "job_id": "ee33b210-93c0-46c6-abea-58841db8dec9",
                                        "title": "Backend Engineer",
                                        "recruiter": {
                                            "id": "eced692c-b5fe-4ebb-b4ca-7faacc0bbc7a",
                                            "name": "Amazon"
                                        },
                                        "job_image": "/media/static/jobs/Screenshot_from_2024-07-01_10-55-13.png",
                                        "location": "Burundi",
                                        "type": "Software",
                                        "salary": 500000,
                                        "is_saved": True
                                    }
                                ]
                            }
                        }
                    )
                ]
            ),
        }
    )


def search_vacancies_docs():
    return extend_schema(
        summary="Search jobs",
        parameters=[
            OpenApiParameter(name="search", type=OpenApiTypes.STR, required=False)
        ],
        description="""
        This endpoint allows an authenticated job recruiter to search for his posted vacancies
        """,
        tags=['Job Recruiter Home'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Successfully retrieved posted vacancies",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved searched vacancies",
                            "data": [
                                {
                                    "id": "ee33b210-93c0-46c6-abea-58841db8dec9",
                                    "title": "Backend Engineer",
                                    "recruiter": {
                                        "id": "eced692c-b5fe-4ebb-b4ca-7faacc0bbc7a",
                                        "full_name": "Amazon"
                                    },
                                    "job_image": "/media/static/jobs/Screenshot_from_2024-07-01_10-55-13.png",
                                    "location": "Burundi",
                                    "type": "Software",
                                    "salary": 500000,
                                    "active": True
                                },
                                {
                                    "id": "9bed0097-7c05-4849-8cfb-b4d28ccaf9c0",
                                    "title": "Software Developer",
                                    "recruiter": {
                                        "id": "eced692c-b5fe-4ebb-b4ca-7faacc0bbc7a",
                                        "full_name": "Amazon"
                                    },
                                    "job_image": "/media/static/jobs/Screenshot_from_2024-07-01_06-53-03.png",
                                    "location": "Åland Islands",
                                    "type": "Software",
                                    "salary": 20000,
                                    "active": True
                                }
                            ]
                        }
                    )
                ]
            ),
        }
    )


def vacancies_home_docs():
    return extend_schema(
        summary="Recruiter home page",
        description="""
        Get home page for job recruiter. This endpoint allows an authenticated job recruiter to search, Retrieve all vacant jobs, and all applicants that applied to jobs posted by the authenticated job recruiter.
        """,
        parameters=[
            OpenApiParameter('active', type=OpenApiTypes.BOOL, description="Filter jobs by active"),
        ],
        tags=["Job Recruiter Home"],
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
                                "profile_name": "Amazon",
                                "vacancies": [
                                    {
                                        "id": "ee33b210-93c0-46c6-abea-58841db8dec9",
                                        "title": "Backend Engineer",
                                        "recruiter": "Amazon",
                                        "job_image": "/media/static/jobs/Screenshot_from_2024-07-01_10-55-13.png",
                                        "location": "Burundi",
                                        "type": "Software",
                                        "salary": 500000,
                                        "active": True
                                    },
                                    {
                                        "id": "9bed0097-7c05-4849-8cfb-b4d28ccaf9c0",
                                        "title": "Software Developer",
                                        "recruiter": "Amazon",
                                        "job_image": "/media/static/jobs/Screenshot_from_2024-07-01_06-53-03.png",
                                        "location": "Åland Islands",
                                        "type": "Software",
                                        "salary": 20000,
                                        "active": True
                                    }
                                ],
                                "all_applied_applicants": [
                                    {
                                        "id": "c57ad787-f80f-4e4f-9062-230637dee27a",
                                        "full_name": "",
                                        "job_title": "Software Developer",
                                        "cv": "/media/Invoice-1CCB6166-0011.pdf"
                                    },
                                    {
                                        "id": "974dfd3c-00ab-4dde-8105-1f50bed62ffd",
                                        "full_name": "",
                                        "job_title": "Backend Engineer",
                                        "cv": "/media/static/applied_files/Receipt-2018-9726.pdf"
                                    }
                                ]
                            }
                        }
                    )
                ]
            ),
        }
    )


def retrieve_all_job_types_docs():
    return extend_schema(
        summary="Retrieve all job types",
        description="""
        This endpoint allows an authenticated job recruiter to retrieve all job types
        """,
        tags=['Job Recruiter Home'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="Successfully retrieved all job types",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully retrieved all job types",
                            "data": [
                                {
                                    "id": "970cc79e-c3bb-47e5-817e-4657d33b0ac2",
                                    "name": "Product"
                                },
                                {
                                    "id": "3b10dad9-8f31-4131-930e-651c9292acfa",
                                    "name": "AI"
                                }
                            ]
                        }
                    )
                ]
            ),
        }
    )


def create_vacancies_docs():
    return extend_schema(
        summary="Create a new job",
        description=(
            """
            This endpoint allows an authenticated job recruiter to create a new job.
            When creating a new job, assign or pass in the country code to the location not the country full name.
            e.g.
            - UK
            - US
            """
        ),
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'image': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Job image file',
                    },
                    'title': {
                        'type': 'string',
                        'description': 'Job title',
                    },
                    'salary': {
                        'type': 'number',
                        'description': 'Salary for the job',
                    },
                    'location': {
                        'type': 'string',
                        'enum': [country.alpha_2 for country in pycountry.countries],
                        'description': 'Location of the job',
                    },
                    'type': {
                        'type': 'string',
                        'description': 'Job type (Primary Key)',
                    },
                    'requirements': {
                        'type': 'array',
                        'items': {
                            'type': 'string'
                        },
                        'description': 'List of job requirements',
                    },
                },
                'required': ['image', 'title', 'salary', 'location', 'type', 'requirements']
            }
        },
        tags=['Job (Recruiter)'],
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response={"application/json"},
                description="Successfully created a new job",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully created a new job",
                            "data": {
                                "id": "8edec3b8-3a6a-483a-8187-9167c44c9410",
                                "title": "Laravel Developer",
                                "job_image": "/media/static/jobs/Screenshot_from_2024-07-01_06-53-03_gHGUICR.png",
                                "recruiter": {
                                    "id": "eced692c-b5fe-4ebb-b4ca-7faacc0bbc7a",
                                    "name": "Amazon"
                                }
                            }
                        }
                    )
                ]
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response={"application/json"},
                description="An error occurred while trying to create a job",
                examples=[
                    OpenApiExample(
                        name="Error Response",
                        value={
                            "status": "failure",
                            "message": "An error occurred while trying to create a job",
                            "code": "other_error",
                        }
                    )
                ]
            )
        }
    )


def update_vacancy_docs():
    return extend_schema(
        summary="Update a job vacancy",
        description=(
            """
            This endpoint allows an authenticated job recruiter to update a job, pass in the id as the path parameter
            If an id is not passed as part of the requirements payload, it's get treated as a new requirement so the requirement gets created
            """
        ),
        tags=['Job (Recruiter)'],
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                response={"application/json"},
                description="Successfully updated a job",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully updated a job",
                            "data": {
                                "id": "8edec3b8-3a6a-483a-8187-9167c44c9410",
                                "title": "React developer",
                                "job_image": "/media/static/jobs/Screenshot_from_2024-07-01_06-53-03_gHGUICR.png",
                                "recruiter": {
                                    "id": "eced692c-b5fe-4ebb-b4ca-7faacc0bbc7a",
                                    "name": "Amazon"
                                }
                            }
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="Job not found",
                examples=[
                    OpenApiExample(
                        name="Error Response",
                        value={
                            "status": "failure",
                            "message": "Job not found",
                            "code": "non-existent",
                        }
                    )
                ]
            ),
        }
    )


def delete_vacancy_docs():
    return extend_schema(
        summary="Delete a job",
        description=(
            """
            This endpoint allows an authenticated job recruiter to delete a job, pass the job id to the path parameter
            """
        ),
        tags=['Job (Recruiter)'],
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                response={"application/json"},
                description="Successfully deleted a job",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully deleted a job",
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="Job not found",
                examples=[
                    OpenApiExample(
                        name="Error Response",
                        value={
                            "status": "failure",
                            "message": "Job not found",
                            "code": "non-existent",
                        }
                    )
                ]
            ),
        }
    )


def update_applied_job_docs():
    return extend_schema(
        summary="Update applied job",
        description=(
            """
            This endpoint allows an authenticated job recruiter to update a posted applied job
            
            ```AVAILABLE FILTERS: PENDING, ACCEPTED, REJECTED, SCHEDULED FOR INTERVIEW```
            """
        ),
        tags=['Job (Recruiter)'],
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                response={"application/json"},
                description="Successfully updated an applied job",
                examples=[
                    OpenApiExample(
                        name="Success Response",
                        value={
                            "status": "success",
                            "message": "Successfully updated an applied job",
                            "data": {
                                "id": "c57ad787-f80f-4e4f-9062-230637dee27a",
                                "job": "Software Developer",
                                "applicant": "Capone Richie",
                                "applicant_image": "/media/static/user_avatars/Screenshot_from_2024-07-01_07-32-00.png",
                                "cv": "/media/CV-1CCB6166-0011.pdf",
                                "status": "SCHEDULED FOR INTERVIEW",
                                "review": "Let's have an interview",
                                "interview_date": "2024-07-09T16:05:21.211000Z"
                            }
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="No application with this ID",
                examples=[
                    OpenApiExample(
                        name="Error Response",
                        value={
                            "status": "failure",
                            "message": "No application with this ID",
                            "code": "non-existent",
                        }
                    )
                ]
            ),
        }
    )
