from django.shortcuts import render

from root.plants.models import Plant

plants = Plant.objects.in_bulk([cid for cid, _ in preds], field_name="class_index")
