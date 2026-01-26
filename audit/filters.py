import django_filters
from .models import AuditEvent


class AuditEventFilter(django_filters.FilterSet):
    date_after = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    date_before = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model = AuditEvent
        fields = ["action", "site"]