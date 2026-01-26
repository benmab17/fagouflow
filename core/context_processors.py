from django.conf import settings


def cloudinary_enabled(request):
    return {"cloudinary_enabled": bool(getattr(settings, "CLOUDINARY_ENABLED", False))}
