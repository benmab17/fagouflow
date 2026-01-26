from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


@register.filter
def avatar_url(user, default_path="img/avatar-default.png"):
    default_url = static(default_path)
    if not user:
        return default_url
    if not getattr(settings, "CLOUDINARY_ENABLED", False):
        return default_url
    avatar = getattr(user, "avatar", None)
    if not avatar:
        return default_url
    try:
        url = avatar.url
    except Exception:
        return default_url
    return url or default_url
