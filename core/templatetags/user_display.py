from django import template

register = template.Library()


@register.filter
def display_name(user):
    if not user:
        return "Utilisateur"
    full = ""
    try:
        full = (user.get_full_name() or "").strip()
    except Exception:
        full = ""
    if full:
        return full
    email = getattr(user, "email", "") or ""
    if email and "@" in email:
        return email.split("@")[0]
    return email or "Utilisateur"
