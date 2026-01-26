from __future__ import annotations

import threading
from typing import Optional

from django.contrib import messages
from django.http import HttpRequest
from django.shortcuts import redirect

_thread_locals = threading.local()


def set_current_request(request: Optional[HttpRequest]) -> None:
    _thread_locals.request = request


def get_current_request() -> Optional[HttpRequest]:
    return getattr(_thread_locals, "request", None)


def get_current_user():
    request = get_current_request()
    if request and hasattr(request, "user"):
        return request.user
    return None


def get_client_ip() -> str:
    request = get_current_request()
    if not request:
        return ""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def get_user_agent() -> str:
    request = get_current_request()
    if not request:
        return ""
    return request.META.get("HTTP_USER_AGENT", "")


class ThreadLocalRequestMiddleware:
    """Store request in thread-local storage for audit logging."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        set_current_request(request)
        response = self.get_response(request)
        set_current_request(None)
        return response


class AdminStaffOnlyMiddleware:
    """Redirect non-staff users away from /admin/."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if request.path.startswith("/admin/"):
            user = getattr(request, "user", None)
            if not (user and user.is_authenticated and user.is_staff):
                messages.error(request, "Accès refusé")
                return redirect("/dashboard/")
        return self.get_response(request)
