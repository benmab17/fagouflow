import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from reports.utils import build_audit_report


class Command(BaseCommand):
    help = "Generate audit report JSON file"

    def add_arguments(self, parser):
        parser.add_argument("--period", choices=["daily", "weekly", "monthly"], required=True)
        parser.add_argument("--date")
        parser.add_argument("--year")
        parser.add_argument("--week")
        parser.add_argument("--month")

    def handle(self, *args, **options):
        period = options["period"]
        params = {k: v for k, v in options.items() if k in {"date", "year", "week", "month"} and v}
        report = build_audit_report(period, params)
        output_dir = Path(settings.REPORTS_OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = output_dir / f"audit_{period}_{report['period']}.json"
        filename.write_text(json.dumps(report, default=str, indent=2))
        self.stdout.write(self.style.SUCCESS(f"Report written to {filename}"))