from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.views import APIView

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.permissions import IsAuthenticatedEmployee
from apps.common.responses import CustomResponse
from apps.misc.models import Tip
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
        tips = Tip.objects.only('title').order_by('?')
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
