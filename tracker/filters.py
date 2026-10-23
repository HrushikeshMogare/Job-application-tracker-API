import django_filters

from .models import JobApplication


class JobApplicationFilter(django_filters.FilterSet):
    applied_after = django_filters.DateFilter(field_name="applied_date", lookup_expr="gte")
    applied_before = django_filters.DateFilter(field_name="applied_date", lookup_expr="lte")

    class Meta:
        model = JobApplication
        fields = ["status", "company", "applied_after", "applied_before"]
