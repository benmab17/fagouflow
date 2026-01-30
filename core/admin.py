from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "country", "created_at", "preview_label")
    search_fields = ("name", "email", "phone")
    exclude = ("preview_only",)

    @admin.display(description="Preview")
    def preview_label(self, obj):
        return "PREVIEW" if getattr(obj, "preview_only", False) else ""
