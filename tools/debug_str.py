import os

import django
from django.apps import apps


def main():
    # Dev tool: validate __str__ across models.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
    django.setup()
    for model in apps.get_models():
        try:
            qs = model.objects.all()[:50]
            for obj in qs:
                if obj is None:
                    continue
                try:
                    val = str(obj)
                    if val is None or val == "None":
                        raise TypeError("Invalid __str__ return")
                except Exception as exc:
                    print(f"BOOM {model._meta.label} pk={getattr(obj, 'pk', None)} => {exc}")
        except Exception as exc:
            print(f"BOOM {model._meta.label} => {exc}")


if __name__ == "__main__":
    main()
