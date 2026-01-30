from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = "Scan __str__ for all models and report non-string/exception cases."

    def handle(self, *args, **options):
        problems = 0
        for model in apps.get_models():
            try:
                qs = model.objects.all()[:50]
            except OperationalError as exc:
                self.stdout.write(f"[SKIP] {model._meta.label} => {exc}")
                continue
            except Exception as exc:
                self.stdout.write(f"[SKIP] {model._meta.label} => {exc}")
                continue

            for obj in qs:
                try:
                    val = str(obj)
                    if val is None or not isinstance(val, str):
                        problems += 1
                        self.stdout.write(
                            f"[BAD __str__] {model._meta.label} pk={getattr(obj, 'pk', None)} => returned None"
                        )
                except Exception as exc:
                    problems += 1
                    self.stdout.write(
                        f"[BAD __str__] {model._meta.label} pk={getattr(obj, 'pk', None)} => {exc}"
                    )

        self.stdout.write(f"Total problems: {problems}")
