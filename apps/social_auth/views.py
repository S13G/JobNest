from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.responses import CustomResponse
from apps.social_auth.serializers import GoogleSocialAuthSerializer


class GoogleSocialAuthView(GenericAPIView):
    serializer_class = GoogleSocialAuthSerializer

    @extend_schema(
        summary="Google Authentication Endpoint",
        description="This endpoint allows users to authenticate through Google",
        request=GoogleSocialAuthSerializer,
        tags=['Social Authentication'],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Success",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Account not found",
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                description="Internal server error",
            )
        }
    )
    def post(self, request):
        """
        Handles POST requests with "auth token" to get user information from Google.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        auth_token = serializer.validated_data['auth_token']

        data = auth_token.get('data')

        if not data:
            raise RequestError(err_code=ErrorCode.SERVER_ERROR,
                               err_msg="Unable to retrieve user data. Please try again later.",
                               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        tokens = auth_token.get('tokens', {})

        return CustomResponse.success(message="Successfully authenticated", data={"tokens": tokens, "data": data},
                                      status_code=status.HTTP_200_OK)
