from django.urls import path
from apps.misc.views import *

urlpatterns = [
    path('tips/all', RetrieveAllTipsView.as_view(), name="retrieve_all_tips"),
    path('tips/<str:tip_id>', RetrieveTipView.as_view(), name="retrieve_tip"),
]