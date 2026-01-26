import django_filters
from .models import ContainerShipment


class ShipmentFilter(django_filters.FilterSet):
    eta_after = django_filters.DateFilter(field_name="eta", lookup_expr="gte")
    eta_before = django_filters.DateFilter(field_name="eta", lookup_expr="lte")

    class Meta:
        model = ContainerShipment
        fields = ["status", "destination_site"]