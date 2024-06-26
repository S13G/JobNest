from django.core.paginator import InvalidPage
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from apps.common.errors import ErrorCode
from apps.common.exceptions import RequestError


class CustomPagination(PageNumberPagination):
    page_size_query_param = "page_size"  # Optional: allow clients to override the page size

    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate a queryset if required, either returning a
        page object, or `None` if pagination is not configured for this view.
        """
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        page_number = self.get_page_number(request, paginator)

        try:
            self.page = paginator.page(page_number)
        except InvalidPage:
            raise RequestError(
                err_code=ErrorCode.INVALID_PAGE, err_msg="Invalid Page", status_code=status.HTTP_404_NOT_FOUND
            )

        self.request = request

        return {
            "items": list(self.page),
            "per_page": page_size,
            "current_page": page_number,
            "last_page": paginator.num_pages,
        }

    def get_paginated_response(self, data):
        return {
            "per_page": self.page.paginator.per_page,
            "current_page": self.page.number,
            "last_page": self.page.paginator.num_pages,
            "items": data,

        }
