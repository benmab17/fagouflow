from django.contrib import admin

from .models import ContainerShipment, ContainerItem, StatusHistory


@admin.register(ContainerShipment)
class ContainerShipmentAdmin(admin.ModelAdmin):
    list_display = ("container_no", "status", "destination_site", "client", "created_at")
    list_filter = ("status", "destination_site", "client")
    search_fields = ("container_no", "bl_no", "client_name", "client__name")


admin.site.register(ContainerItem)
admin.site.register(StatusHistory)
