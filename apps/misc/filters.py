from django_filters import FilterSet, filters

from apps.misc.models import FAQType


class FAQFilter(FilterSet):
    type = filters.ChoiceFilter(
        field_name='type__name',
        lookup_expr='exact',
        choices=lambda: [(type_obj.name, type_obj.name) for type_obj in FAQType.objects.all()]
    )
