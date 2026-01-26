from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .utils import build_audit_report


class IsBossOrHQ(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role in {"BOSS", "HQ_ADMIN"}


class AuditReportViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsBossOrHQ]

    @action(detail=False, methods=["get"], url_path="daily")
    def daily(self, request):
        date_value = request.query_params.get("date")
        if not date_value:
            return Response({"detail": "date is required"}, status=400)
        report = build_audit_report("daily", {"date": date_value})
        return Response(report)

    @action(detail=False, methods=["get"], url_path="weekly")
    def weekly(self, request):
        year = request.query_params.get("year")
        week = request.query_params.get("week")
        if not year or not week:
            return Response({"detail": "year and week are required"}, status=400)
        report = build_audit_report("weekly", {"year": year, "week": week})
        return Response(report)

    @action(detail=False, methods=["get"], url_path="monthly")
    def monthly(self, request):
        year = request.query_params.get("year")
        month = request.query_params.get("month")
        if not year or not month:
            return Response({"detail": "year and month are required"}, status=400)
        report = build_audit_report("monthly", {"year": year, "month": month})
        return Response(report)
