from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.permissions import IsAuthenticatedEmployee
from apps.common.responses import CustomResponse
from apps.misc.docs.docs import *
from apps.misc.filters import FAQFilter
from apps.misc.models import Tip, FAQ, FAQType
from apps.misc.serializers import TipSerializer
from utilities.caching import get_cached_data, set_cached_data


# Create your views here.


class RetrieveAllTipsView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @retrieve_all_tips_docs()
    def get(self, request):
        cache_key = "retrieve_tips"
        cached_data = get_cached_data(cache_key=cache_key)

        if cached_data:
            return CustomResponse.success(message="Tips retrieved successfully", data=cached_data)

        tips = Tip.objects.only('title').order_by('-created')

        data = [
            {
                "id": tip.id,
                "title": tip.title,
                "author_image": tip.author_image_url
            }
            for tip in tips
        ]

        set_cached_data(cache_key=cache_key, data=data, timeout=60 * 60 * 24 * 5)

        return CustomResponse.success(message="Tips retrieved successfully", data=data)


class RetrieveTipView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @retrieve_tip_docs()
    def get(self, request, *args, **kwargs):
        tip_id = kwargs.get('tip_id')

        cache_key = f"retrieve_tip_{tip_id}"
        cached_data = get_cached_data(cache_key=cache_key)

        if cached_data:
            return CustomResponse.success(message="Tip retrieved successfully", data=cached_data)

        try:
            tip = Tip.objects.get(id=tip_id)
        except Tip.DoesNotExist:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No tip found for this id",
                               status_code=status.HTTP_404_NOT_FOUND)

        data = TipSerializer(tip).data

        set_cached_data(cache_key=cache_key, data=data, timeout=60 * 60 * 24 * 5)

        return CustomResponse.success(message="Tip retrieved successfully", data=data)


class RetrieveAllFAQTypesView(APIView):
    permission_classes = (IsAuthenticated,)

    @retrieve_all_faq_types_docs()
    def get(self, request):
        cache_key = "retrieve_faqs_types"
        cached_data = get_cached_data(cache_key=cache_key)

        if cached_data:
            return CustomResponse.success(message="FAQ types retrieved successfully", data=cached_data)

        queryset = FAQType.objects.only('id', 'name')

        data = [
            {
                "id": faq_type.id,
                "name": faq_type.name
            }
            for faq_type in queryset
        ]

        set_cached_data(cache_key=cache_key, data=data, timeout=60 * 60 * 24 * 7)

        return CustomResponse.success(message="FAQ types retrieved successfully", data=data)


class FilterAllFAQsView(APIView):
    permission_classes = (IsAuthenticated,)
    filterset_class = FAQFilter
    filter_backends = [DjangoFilterBackend]

    @filter_all_faqs_docs()
    def get(self, request):
        query_params = request.GET.urlencode()
        cache_key = f"retrieve_faqs_{query_params}"
        cached_data = get_cached_data(cache_key=cache_key)

        if cached_data:
            return CustomResponse.success(message="FAQs filtered successfully", data=cached_data)

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

        set_cached_data(cache_key=cache_key, data=data, timeout=60 * 60 * 24 * 7)
        return CustomResponse.success(message="FAQs filtered successfully", data=data)
