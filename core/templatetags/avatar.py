from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


@register.filter
def avatar_url(user, default_path="img/avatar-default.png"):
    default_url = static(default_path)
    if not user:
        return default_url
    cloudinary_enabled = getattr(settings, "CLOUDINARY_ENABLED", False)
    if cloudinary_enabled:
        avatar = getattr(user, "avatar", None)
        if avatar:
            try:
                url = avatar.url
                if url:
                    return url
            except Exception:
                pass
    local_avatar = getattr(user, "local_avatar", None)
    if local_avatar:
        try:
            url = local_avatar.url
            if url:
                return url
        except Exception:
            pass
    return default_url
