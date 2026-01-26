from django.contrib import admin

from .models import ContainerShipment, ContainerItem, StatusHistory

admin.site.register(ContainerShipment)
admin.site.register(ContainerItem)
admin.site.register(StatusHistory)