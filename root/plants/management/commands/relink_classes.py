"""Django management command. Save as plants/management/commands/relink_classes.py
(also create empty __init__.py files in plants/management/ and plants/management/commands/).

Makes Plant.class_index follow the class order stored inside the trained checkpoint, so that what the model
predicts (a position 0..N-1 in its class list) points at the right database row.

    python manage.py relink_classes            # only prints the plan, changes nothing
    python manage.py relink_classes --apply    # writes it (copy db.sqlite3 first!)
    python manage.py relink_classes --ckpt ml_models/efficientnet_b0_best.pt --apply

Rows for plants the model cannot predict stay in the catalogue; their class_index is cleared (or parked at
100000 + id when the column cannot be NULL) so that no number below the model's class count is shared.
"""
import os

import torch
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from plants.models import Plant

# model class id -> slug of the EXISTING database row (each link was checked against the dataset's species names)
LINK = {
    "aloevera": "aloe_vera",
    "betel": "betel",
    "catharanthus": "catharanthus",
    "guava": "guava",
    "jamun": "jamun",
    "mint": "mentha",
    "neem": "neem",
    "parijata": "nyctanthes",
    "tulsi": "tulsi",
}
LINK_COMMON = {"aloevera": "Aloe vera"}        # filled in only when the existing row has no common name

# model class id -> (common name, scientific name) for classes that have no row yet. They are created WITHOUT any
# medicinal text. A blank scientific name means the regional name is not verified yet: do not guess it.
NEW = {
    "amla": ("Amla", "Phyllanthus emblica"),
    "ashwagandha": ("Ashwagandha", "Withania somnifera"),
    "castor": ("Castor", "Ricinus communis"),
    "curry": ("Curry leaf", "Murraya koenigii"),
    "drumstick": ("Drumstick", "Moringa oleifera"),
    "papaya": ("Papaya", "Carica papaya"),
    "pomegranate": ("Pomegranate", "Punica granatum"),
    "brahmi": ("Brahmi", ""),
    "amruthaballi": ("Amruthaballi", ""),
    "ekka": ("Ekka", ""),
    "insulin": ("Insulin plant", ""),
}
PARK = 100000


class Command(BaseCommand):
    help = "Make Plant.class_index follow the order of the classes stored in the checkpoint."

    def add_arguments(self, parser):
        parser.add_argument("--ckpt", default=os.path.join("ml_models", "efficientnet_b0_best.pt"),
                            help="checkpoint path, absolute or relative to BASE_DIR")
        parser.add_argument("--apply", action="store_true", help="write the changes (default: print the plan only)")

    def handle(self, *args, **options):
        ckpt = options["ckpt"]
        if not os.path.isabs(ckpt):
            ckpt = os.path.join(str(settings.BASE_DIR), ckpt)
        classes = torch.load(ckpt, map_location="cpu")["classes"]
        existing = {p.slug: p for p in Plant.objects.all()}

        plan = []                                   # (position, class id, target slug)
        for i, cid in enumerate(classes):
            if cid in LINK:
                slug = LINK[cid]
                if slug not in existing:
                    raise CommandError(f"class '{cid}' should link to database slug '{slug}', which does not exist")
            elif cid in NEW:
                slug = cid
            else:
                raise CommandError(f"no rule for model class '{cid}': add it to LINK or NEW in this file")
            plan.append((i, cid, slug))

        for i, cid, slug in plan:
            what = (f"existing row '{slug}' (id {existing[slug].id})" if slug in existing else "NEW row")
            self.stdout.write(f"{i:>3}  {cid:<14} -> {what}")
        keep = {slug for _, _, slug in plan}
        left = sorted(s for s in existing if s not in keep)
        self.stdout.write(f"\n{len(left)} existing plants stay in the catalogue but are no longer predicted: "
                          f"{', '.join(left) or 'none'}")
        if not options["apply"]:
            self.stdout.write("\nDry run only: nothing was changed. Back up db.sqlite3, then run again with --apply.")
            return

        nullable = Plant._meta.get_field("class_index").null
        with transaction.atomic():
            # 1. park every row on a unique temporary number so the new numbers cannot collide
            rows = list(Plant.objects.all())
            for p in rows:
                p.class_index = PARK + p.id
            Plant.objects.bulk_update(rows, ["class_index"])
            by_slug = {p.slug: p for p in rows}
            # 2. give each class its position in the checkpoint
            for i, cid, slug in plan:
                p = by_slug.get(slug)
                if p is None:
                    common, sci = NEW[cid]
                    p = Plant(slug=slug, common_name=common, scientific_name=sci)
                elif not p.common_name and cid in LINK_COMMON:
                    p.common_name = LINK_COMMON[cid]
                p.class_index = i
                p.save()
            # 3. plants the model cannot predict
            if nullable:
                Plant.objects.exclude(slug__in=keep).update(class_index=None)
        n = Plant.objects.filter(class_index__gte=0, class_index__lt=len(classes)).count()
        self.stdout.write(f"\ndone: {n} of {len(classes)} model classes now point at a database row.")
        if n != len(classes):
            raise CommandError("count mismatch after update; check the Plant table")