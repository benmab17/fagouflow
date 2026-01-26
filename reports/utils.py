from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, Any

from django.db.models import Count
from django.utils import timezone

from audit.models import AuditEvent


def _date_range_for_period(period: str, params: Dict[str, Any]):
    if period == "daily":
        target = date.fromisoformat(params["date"])
        start = datetime.combine(target, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        label = target.isoformat()
    elif period == "weekly":
        year = int(params["year"])
        week = int(params["week"])
        start = datetime.fromisocalendar(year, week, 1).replace(tzinfo=timezone.utc)
        end = start + timedelta(days=7)
        label = f"{year}-W{week:02d}"
    elif period == "monthly":
        year = int(params["year"])
        month = int(params["month"])
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        label = f"{year}-{month:02d}"
    else:
        raise ValueError("Invalid period")
    return start, end, label


def build_audit_report(period: str, params: Dict[str, Any]):
    """Build aggregated audit metrics for a time period."""
    start, end, label = _date_range_for_period(period, params)
    base_qs = AuditEvent.objects.filter(created_at__gte=start, created_at__lt=end)

    events_by_action = dict(base_qs.values("action").annotate(count=Count("id")).values_list("action", "count"))
    events_by_site = dict(base_qs.values("site").annotate(count=Count("id")).values_list("site", "count"))
    top_users = list(
        base_qs.values("actor__email")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    last_events = list(
        base_qs.order_by("-created_at")[:50].values("id", "action", "entity_type", "entity_id", "site", "summary", "created_at")
    )

    return {
        "period": label,
        "total_events": base_qs.count(),
        "events_by_action": events_by_action,
        "events_by_site": events_by_site,
        "top_users": top_users,
        "last_events": last_events,
    }
