from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError
from apps.common.permissions import IsAuthenticatedEmployee
from apps.common.responses import CustomResponse
from apps.misc.docs.docs import *
from apps.misc.filters import FAQFilter
from apps.misc.models import Tip, FAQ, FAQType
from apps.misc.serializers import TipSerializer


# Create your views here.


class RetrieveAllTipsView(APIView):
    permission_classes = (IsAuthenticatedEmployee,)

    @retrieve_all_tips_docs()
    @method_decorator(cache_page(60 * 60 * 24 * 5, key_prefix="retrieve_tips"))
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

    @retrieve_tip_docs()
    @method_decorator(cache_page(60 * 60 * 24 * 5, key_prefix="retrieve_tip"))
    def get(self, request, *args, **kwargs):
        tip_id = kwargs.get('tip_id')

        try:
            tip = Tip.objects.get(id=tip_id)
        except Tip.DoesNotExist:
            raise RequestError(err_code=ErrorCode.NON_EXISTENT, err_msg="No tip found for this id",
                               status_code=status.HTTP_404_NOT_FOUND)

        data = TipSerializer(tip).data
        return CustomResponse.success(message="Tip retrieved successfully", data=data)


class RetrieveAllFAQTypesView(APIView):
    permission_classes = (IsAuthenticated,)

    @retrieve_all_faq_types_docs()
    @method_decorator(cache_page(60 * 60 * 24 * 7, key_prefix="retrieve_faqs_types"))
    def get(self, request):
        queryset = FAQType.objects.only('id', 'name')

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

    @filter_all_faqs_docs()
    @method_decorator(cache_page(60 * 60 * 24 * 7, key_prefix="retrieve_faqs"))
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
