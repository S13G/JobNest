from django_filters import FilterSet, filters

from apps.jobs.choices import STATUS_CHOICES
from apps.jobs.models import JobType


class JobFilter(FilterSet):
    type = filters.ChoiceFilter(
        field_name='type__name',
        lookup_expr='icontains',
        choices=[(type_obj.name, type_obj.name) for type_obj in JobType.objects.all()]
    )
    salary_min = filters.NumericRangeFilter(field_name='salary', lookup_expr='gte')
    salary_max = filters.NumericRangeFilter(field_name='salary', lookup_expr='lte')
    location = filters.CharFilter(field_name='location', lookup_expr='icontains')


class AppliedJobFilter(FilterSet):
    status = filters.ChoiceFilter(field_name='status', choices=STATUS_CHOICES)


class VacanciesFilter(FilterSet):
    active = filters.BooleanFilter(field_name="active")
