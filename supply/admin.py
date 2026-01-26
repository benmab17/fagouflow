from django.contrib import admin

from .models import Supplier, Product, PurchaseOrder, PurchaseOrderLine

admin.site.register(Supplier)
admin.site.register(Product)
admin.site.register(PurchaseOrder)
admin.site.register(PurchaseOrderLine)