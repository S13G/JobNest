from django_filters import filters, FilterSet


class ChatFilter(FilterSet):
    is_read = filters.BooleanFilter(field_name="is_read")
