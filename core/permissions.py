from typing import Iterable


def user_can_access_site(user, site: str | None) -> bool:
    if site is None:
        return True
    return user.role in {"BOSS", "HQ_ADMIN"} or user.site == site


def filter_queryset_by_site(queryset, user, site_fields: Iterable[str]):
    if user.role in {"BOSS", "HQ_ADMIN"}:
        return queryset
    for field in site_fields:
        if hasattr(queryset.model, field):
            return queryset.filter(**{field: user.site})
    return queryset