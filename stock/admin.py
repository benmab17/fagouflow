from django.contrib import admin

from .models import StockLocation, StockMovement, Sale, SaleLine

admin.site.register(StockLocation)
admin.site.register(StockMovement)
admin.site.register(Sale)
admin.site.register(SaleLine)