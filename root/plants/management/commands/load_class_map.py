import csv
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from plants.models import Plant

# "Tulsi (Ocimum tenuiflorum)" -> common="Tulsi", scientific="Ocimum tenuiflorum"
NAME_RE = re.compile(r"^(.*?)\s*\((.*)\)\s*$")


class Command(BaseCommand):
    help = "Load plants from class_map.csv (skips # comments, merges duplicate classes)"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", nargs="?", default="data/class_map.csv")
        parser.add_argument(
            "--order", choices=["alphabetical", "csv"], default="alphabetical",
            help="How model output numbers are assigned. Must match training.",
        )

    def handle(self, *args, **opts):
        path = Path(opts["csv_path"])
        if not path.exists():
            raise CommandError(f"File not found: {path}")

        entries = {}  # slug -> display_name (first occurrence wins)
        with open(path, newline="", encoding="utf-8-sig") as f:
            for raw in csv.DictReader(f):
                slug = (raw.get("class_id") or "").strip()
                if not slug or slug.startswith("#"):
                    continue
                if slug not in entries:
                    entries[slug] = (raw.get("display_name") or "").strip()

        if not entries:
            raise CommandError("No classes found in the CSV")

        slugs = list(entries)
        if opts["order"] == "alphabetical":
            slugs.sort()

        with transaction.atomic():
            Plant.objects.update(class_index=None)  # avoid unique clashes when re-running
            for idx, slug in enumerate(slugs):
                display = entries[slug]
                m = NAME_RE.match(display)
                if m:
                    common, sci = m.group(1).strip(), m.group(2).strip()
                else:
                    common, sci = "", display or slug
                Plant.objects.update_or_create(
                    slug=slug,
                    defaults={"class_index": idx, "scientific_name": sci, "common_name": common},
                )
                self.stdout.write(f"  {idx:>2}  {slug:<14} {sci}")

        self.stdout.write(self.style.SUCCESS(
            f"Done. {len(slugs)} plants loaded (order: {opts['order']})."
        ))