from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter
from rest_framework import status

from apps.misc.models import FAQType


def retrieve_all_tips_docs():
    return extend_schema(
        summary="Retrieve all tips",
        description=
        """
        This endpoint allows a user to retrieve all tips.
        """,
        tags=['Tips'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Tips retrieved successfully",
                response={"application/json"},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Tips retrieved successfully",
                            "data": [
                                {
                                    "id": "07ad4a3e-dee3-4c92-9eb0-490886a879fd",
                                    "title": "How to secure a job",
                                    "author_image": "/media/static/tip_author/2024-07-01_06-53-03.png"
                                }
                            ]
                        }
                    )
                ]
            )
        }
    )


def retrieve_tip_docs():
    return extend_schema(
        summary="Retrieve tip",
        description=
        """
        This endpoint allows a user to retrieve a tip.
        """,
        tags=['Tips'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Tip retrieved successfully",
                response={"application/json"},
                examples=[
                    OpenApiExample(
                        name="Success response",
                        value={
                            "status": "success",
                            "message": "Tip retrieved successfully",
                            "data": {
                                "id": "07ad4a3e-dee3-4c92-9eb0-490886a879fd",
                                "title": "How to secure a job",
                                "description": "Lorem ipsum way",
                                "author": "John Doe",
                                "author_image": "/media/static/tip_author/2024-07-01_06-53-03.png",
                                "position": "Senior Software Engineer"
                            }
                        }
                    )
                ]
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response={"application/json"},
                description="No tip found for this id",
                examples=[
                    OpenApiExample(
                        name="Not found",
                        value={
                            "status": "failure",
                            "message": "No tip found for this id",
                            "code": "non_existent"
                        }
                    )
                ]
            )
        }
    )


def retrieve_all_faq_types_docs():
    return extend_schema(
        summary="Retrieve all FAQ types",
        description=
        """
        This endpoint allows a user to retrieve all FAQ types.
        """,
        tags=['FAQs'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={"application/json"},
                description="FAQ types retrieved successfully",
                examples=[
                    OpenApiExample(
                        name="FAQ types",
                        value={
                            "status": "success",
                            "message": "FAQ types retrieved successfully",
                            "data": [
                                {
                                    "id": "6974c55b-6b9e-4dcd-98d1-440219471061",
                                    "name": "Account"
                                },
                                {
                                    "id": "c925e7aa-74b5-49b9-ae7c-560e31740db2",
                                    "name": "Login"
                                }
                            ]
                        }
                    )
                ]
            ),
        }
    )


def filter_all_faqs_docs():
    return extend_schema(
        summary="Filter all FAQs",
        description=(
            """
            This endpoint allows a user to filter all FAQs.
            
            ```MAKE SURE YOU CALL THE RETRIEVE ALL FAQs TYPES ENDPOINT BEFORE CALLING THIS ENDPOINT```
            
            So you'll know which filter exists and you must pass them the same way(case sensitive) to the query string.
            """
        ),
        tags=['FAQs'],
        parameters=[
            OpenApiParameter('type', OpenApiTypes.STR, description="Filter FAQs by type",
                             enum=FAQType.objects.values_list('name', flat=True))
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="FAQs filtered successfully",
                examples=[
                    OpenApiExample(
                        name="FAQs",
                        value={
                            "status": "success",
                            "message": "FAQs filtered successfully",
                            "data": [
                                {
                                    "id": "e797954a-cf8a-4f51-8d78-c680efd5c14e",
                                    "question": "How to logout from jobetude",
                                    "answer": "You can do that directly from your profile"
                                },
                                {
                                    "id": "5b63ea2b-69cd-4c7d-b2d4-7b698e1d16e2",
                                    "question": "What is JobNest",
                                    "answer": "Jobetude is greatest job portal platform in this century. \r\nIt helps student to find a job quick in their area."
                                }
                            ]
                        }
                    )
                ]
            )
        }
    )
