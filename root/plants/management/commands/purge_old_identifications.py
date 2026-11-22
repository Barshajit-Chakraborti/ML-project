from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from plants.models import Identification


class Command(BaseCommand):
    help = "Delete uploads that never received feedback and are older than --days"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30)

    def handle(self, *args, **opts):
        cutoff = timezone.now() - timedelta(days=opts["days"])
        qs = Identification.objects.filter(created__lt=cutoff, feedback__isnull=True)
        count = qs.count()
        qs.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} uploads older than {opts['days']} days."))