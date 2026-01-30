from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "full_name_label", "role_label", "site_label", "client_label", "is_active", "avatar_label")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name", "role", "site", "client", "avatar")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "full_name", "role", "site", "client", "avatar", "password1", "password2")}),
    )
    search_fields = ("email", "full_name")

    def _strip_avatar(self, fields):
        return tuple(f for f in fields if f != "avatar")

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if not getattr(settings, "CLOUDINARY_ENABLED", False):
            new_fieldsets = []
            for name, opts in fieldsets:
                fields = opts.get("fields", ())
                opts = dict(opts)
                opts["fields"] = self._strip_avatar(fields)
                new_fieldsets.append((name, opts))
            return new_fieldsets
        return fieldsets

    def get_add_fieldsets(self, request):
        fieldsets = super().get_add_fieldsets(request)
        if not getattr(settings, "CLOUDINARY_ENABLED", False):
            new_fieldsets = []
            for name, opts in fieldsets:
                fields = opts.get("fields", ())
                opts = dict(opts)
                opts["fields"] = self._strip_avatar(fields)
                new_fieldsets.append((name, opts))
            return new_fieldsets
        return fieldsets

    @admin.display(description="Nom")
    def full_name_label(self, obj):
        val = getattr(obj, "full_name", None)
        return val if val else "-"

    @admin.display(description="Rôle")
    def role_label(self, obj):
        val = getattr(obj, "role", None)
        return val if val else "-"

    @admin.display(description="Site")
    def site_label(self, obj):
        val = getattr(obj, "site", None)
        return val if val else "-"

    @admin.display(description="Client")
    def client_label(self, obj):
        try:
            client = getattr(obj, "client", None)
            if client:
                return str(client)
        except Exception:
            pass
        return "-"

    @admin.display(description="Avatar")
    def avatar_label(self, obj):
        try:
            avatar = getattr(obj, "avatar", None)
            if avatar:
                return "Oui"
        except Exception:
            pass
        return "Non"
