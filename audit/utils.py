from typing import Any, Dict

from django.forms.models import model_to_dict


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    for key in ["password", "last_login"]:
        data.pop(key, None)
    return data


def serialize_instance(instance) -> Dict[str, Any]:
    """Serialize a model instance to a sanitized dict."""
    data = model_to_dict(instance)
    return sanitize_dict(data)
