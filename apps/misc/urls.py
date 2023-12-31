from django.urls import path
from apps.misc.views import *

urlpatterns = [
    path('tips/all', RetrieveAllTipsView.as_view(), name="retrieve-all-tips"),
    path('tips/<str:tip_id>', RetrieveTipView.as_view(), name="retrieve-tip"),
    path('faqs', FilterAllFAQsView.as_view(), name="filter-all-faqs"),
    path('faq/types', RetrieveAllFAQTypesView.as_view(), name="retrieve-all-faqs-types"),
]