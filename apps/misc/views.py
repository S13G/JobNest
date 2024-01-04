from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiExample
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.permissions import IsAuthenticatedEmployee, IsAuthenticatedCompany
from apps.common.responses import CustomResponse
from apps.misc.filters import FAQFilter
from apps.misc.models import Tip, FAQ, FAQType
from apps.misc.serializers import TipSerializer


# Create your views here.


class RetrieveAllTipsView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @extend_schema(
        summary="Retrieve all tips",
        description=(
                """
                This endpoint allows a user to retrieve all tips.
                """
        ),
        tags=['Tips'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Tips retrieved successfully",
                response=TipSerializer(many=True)
            )
        }
    )
    def get(self, request):
        tips = Tip.objects.only('title').order_by('-created')
        data = [
            {
                "id": tip.id,
                "title": tip.title,
                "author_image": tip.author_image_url
            }
            for tip in tips
        ]
        return CustomResponse.success(message="Tips retrieved successfully", data=data)


class RetrieveTipView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @extend_schema(
        summary="Retrieve tip",
        description=(
                """
                This endpoint allows a user to retrieve a tip.
                """
        ),
        tags=['Tips'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Tip retrieved successfully",
                response=TipSerializer
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="No tip found for this id",
            )
        }
    )
    def get(self, request, *args, **kwargs):
        tip_id = self.kwargs.get('tip_id')

        try:
            tip = Tip.objects.get(id=tip_id)
        except Tip.DoesNotExist:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No tip found for this id",
                               status_code=status.HTTP_404_NOT_FOUND)

        serializer = TipSerializer(tip)
        return CustomResponse.success(message="Tip retrieved successfully", data=serializer.data)


class RetrieveAllFAQTypesView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Retrieve all FAQ types",
        description=(
                """
                This endpoint allows a user to retrieve all FAQ types.
                """
        ),
        tags=['FAQs'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="FAQ types retrieved successfully",
            ),
        }
    )
    def get(self, request):
        queryset = FAQType.objects.all()
        data = [
            {
                "id": faq_type.id,
                "name": faq_type.name
            }
            for faq_type in queryset
        ]
        return CustomResponse.success(message="FAQ types retrieved successfully", data=data)


class FilterAllFAQsView(APIView):
    permission_classes = (IsAuthenticated,)
    filterset_class = FAQFilter
    filter_backends = [DjangoFilterBackend]

    @extend_schema(
        summary="Filter all FAQs",
        description=(
                """
                This endpoint allows a user to filter all FAQs.
                """
        ),
        tags=['FAQs'],
        parameters=[
            OpenApiParameter('type', OpenApiTypes.STR, required=False, description="Filter FAQs by type")
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="FAQs filtered successfully",
            )
        }
    )
    def get(self, request):
        queryset = FAQ.objects.select_related('type').all().order_by('question')
        queryset = self.filterset_class(data=request.GET, queryset=queryset).qs
        data = [
            {
                "id": faq.id,
                "question": faq.question,
                "answer": faq.answer,
            }
            for faq in queryset
        ]
        return CustomResponse.success(message="FAQs filtered successfully", data=data)
